"""PostgreSQL regression checks for schema-lock/index-build interaction.

Run with the app dependencies installed and PGHOST/PGPORT/PGUSER/PGPASSWORD
pointing to a test server (the role needs CREATEDB):

    python scripts/ci/cache_schema_lock_test.py

Each run creates and drops its own database. No Redis or Augur connection is used.
"""

import os
import sys
import threading
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import psycopg2 as pg
from psycopg2 import sql
from psycopg2.extensions import make_dsn

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "8Knot" / "cache_manager"))
# cx_common requires these at import time; the tests never connect to Augur.
with patch.dict(os.environ, {f"AUGUR_{key}": "unused" for key in ("USERNAME", "PASSWORD", "HOST", "PORT", "DATABASE")}):
    import db_init


class CacheSchemaLockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = f"cache_lock_test_{uuid.uuid4().hex}"
        cls.dsn = make_dsn(dbname=cls.database, options="-c statement_timeout=10000")
        with closing(pg.connect(dbname="postgres")) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(cls.database)))

    @classmethod
    def tearDownClass(cls):
        with closing(pg.connect(dbname="postgres")) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(cls.database)))

    def setUp(self):
        # Name real PostgreSQL connections so the observer can see the waiter.
        factory = patch.object(
            db_init,
            "_connect_with_retry",
            side_effect=lambda _: pg.connect(self.dsn, application_name=threading.current_thread().name),
        )
        factory.start()
        self.addCleanup(factory.stop)

    def test_waiter_does_not_block_concurrent_index(self):
        entered = threading.Event()

        def wait_for_lock():
            with db_init._cache_schema_lock():
                entered.set()

        with (
            closing(pg.connect(self.dsn)) as observer,
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="cache-lock-waiter") as executor,
        ):
            observer.autocommit = True
            with observer.cursor() as cur:
                cur.execute("CREATE TABLE index_target (repo_id int)")
                try:
                    with db_init._cache_schema_lock():
                        waiter = executor.submit(wait_for_lock)
                        # Wait until the second initializer has attempted the lock,
                        # whether it uses the old blocking call or the fixed retry.
                        deadline = time.monotonic() + 5
                        while time.monotonic() < deadline:
                            cur.execute(
                                """
                                SELECT backend_xmin FROM pg_stat_activity
                                WHERE datname = current_database()
                                  AND application_name LIKE 'cache-lock-waiter%%'
                                  AND query LIKE 'SELECT pg_%%advisory_lock%%'
                                """
                            )
                            if cur.fetchone() is not None:
                                break
                            time.sleep(0.01)
                        else:
                            self.fail("Second initializer never attempted the schema lock")

                        self.assertFalse(entered.is_set(), "Schema lock did not exclude the second initializer")
                        # The old blocking lock retains a snapshot: this command
                        # times out instead of completing while the waiter exists.
                        cur.execute("SET statement_timeout = '3s'")
                        cur.execute("CREATE INDEX CONCURRENTLY index_target_repo_idx ON index_target (repo_id)")
                        self.assertFalse(entered.is_set(), "Waiter acquired the schema lock before its release")
                        cur.execute(
                            "SELECT indisvalid FROM pg_index WHERE indexrelid = 'index_target_repo_idx'::regclass"
                        )
                        self.assertTrue(cur.fetchone()[0])

                    waiter.result(timeout=5)
                    self.assertTrue(entered.is_set(), "Waiter did not acquire the released schema lock")
                finally:
                    # A timed-out future may still be polling. Disconnect it
                    # before the executor waits for its thread to finish.
                    cur.execute(
                        """
                        SELECT pg_terminate_backend(pid) FROM pg_stat_activity
                        WHERE datname = current_database()
                          AND application_name LIKE 'cache-lock-waiter%%'
                        """
                    )

    def test_lock_released_after_error(self):
        with self.assertRaisesRegex(RuntimeError, "initialization failed"):
            with db_init._cache_schema_lock():
                raise RuntimeError("initialization failed")

        with closing(pg.connect(self.dsn)) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SELECT pg_try_advisory_lock(hashtext(%s))", ("8knot-cache-schema-init",))
                self.assertTrue(cur.fetchone()[0], "Schema lock leaked after an initialization error")


if __name__ == "__main__":
    unittest.main()
