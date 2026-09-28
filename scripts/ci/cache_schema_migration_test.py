"""PostgreSQL integration checks for forward-only cache schema versioning.

Run with app dependencies installed and PGHOST/PGPORT/PGUSER/PGPASSWORD
pointing to a test server (the role needs CREATEDB):

    python scripts/ci/cache_schema_migration_test.py

Each test uses its own database and temporary copy of the migration environment.
Only Redis synchronization is stubbed; startup and Alembic use real PostgreSQL.
"""

import os
import shutil
import site
import subprocess
import sys
import tempfile
import unittest
import uuid
from contextlib import closing
from pathlib import Path

import psycopg2 as pg
from alembic.config import Config
from alembic.script import ScriptDirectory
from psycopg2 import sql


CACHE_MANAGER = Path(__file__).resolve().parents[2] / "8Knot" / "cache_manager"


class CacheSchemaMigrationTest(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="cache migrations ")
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name)
        self.cache_manager = self.workspace / "source tree" / "cache_manager"
        shutil.copytree(CACHE_MANAGER, self.cache_manager, ignore=shutil.ignore_patterns("__pycache__"))
        self.config = self.cache_manager / "alembic.ini"
        self.database = f"cache_migration_test_{uuid.uuid4().hex}"
        with closing(pg.connect(dbname="postgres")) as conn:
            params = conn.get_dsn_parameters()
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database)))
        self.addCleanup(self.drop_database)
        self.env = {
            **os.environ,
            **{f"AUGUR_{key}": "unused" for key in ("USERNAME", "PASSWORD", "HOST", "PORT", "DATABASE")},
            "CACHE_DB_NAME": self.database,
            "CACHE_HOST": params["host"],
            "CACHE_PORT": params["port"],
            "CACHE_USER": params["user"],
            "POSTGRES_PASSWORD": os.getenv("PGPASSWORD", ""),
        }

    def drop_database(self):
        with closing(pg.connect(dbname="postgres")) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(self.database)))

    def query(self, statement):
        with closing(pg.connect(dbname=self.database)) as conn:
            with conn.cursor() as cur:
                cur.execute(statement)
                rows = cur.fetchall() if cur.description else None
            conn.commit()
            return rows

    def run_python(self, code):
        # Load dependencies without editable-install paths, which could hide
        # broken package resolution in the copied Alembic environment.
        dependencies = site.getsitepackages() + [site.getusersitepackages()]
        result = subprocess.run(
            [sys.executable, "-I", "-S", "-c", f"import sys; sys.path.extend({dependencies!r}); " + code],
            cwd=self.workspace,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_db_init(self, expression="raise SystemExit(db_init.db_init())"):
        self.run_python(
            f"import sys; sys.path.insert(0, {str(self.cache_manager)!r}); "
            "import db_init; db_init._synchronize_redis_broker = lambda _: None; " + expression,
        )

    def seed_current_cache(self):
        self.run_db_init("db_init._create_application_tables()")
        self.query("INSERT INTO issues_query (repo_id, issue, labels) VALUES (42, 7, 'bug')")
        self.query("INSERT INTO cache_bookkeeping (cache_func, repo_id) VALUES ('issues_query', 42)")

    def assert_cached_data_preserved(self):
        self.assertEqual(self.query("SELECT repo_id, issue, labels FROM issues_query"), [(42, 7, "bug")])
        self.assertEqual(self.query("SELECT cache_func, repo_id FROM cache_bookkeeping"), [("issues_query", 42)])

    def add_future_revision(self):
        (self.cache_manager / "migrations" / "versions" / "2_test_change.py").write_text(
            'from alembic import op\nrevision = "2"\ndown_revision = "1"\n'
            "def upgrade():\n"
            '    op.execute("ALTER TABLE issues_query ADD COLUMN migration_marker text")\n'
            "    op.execute(\"UPDATE issues_query SET migration_marker = 'applied'\")\n"
            "def downgrade():\n"
            '    op.execute("ALTER TABLE issues_query DROP COLUMN migration_marker")\n'
        )
        # A future release must also update the fresh-cache CREATE definition.
        init_script = self.cache_manager / "db_init.py"
        init_script.write_text(
            init_script.read_text().replace("labels text\n", "labels text,\n                migration_marker text\n")
        )

    def assert_future_upgrade(self):
        self.add_future_revision()
        self.run_db_init()
        # A second startup must not reapply the non-idempotent ADD COLUMN.
        self.run_db_init()
        self.assertEqual(self.query("SELECT version_num FROM alembic_version"), [("2",)])
        self.assertEqual(self.query("SELECT migration_marker FROM issues_query"), [("applied",)])
        self.assert_cached_data_preserved()

    def test_existing_cache_adopts_baseline_without_losing_data(self):
        self.seed_current_cache()
        self.run_db_init()
        self.assertEqual(self.query("SELECT version_num FROM alembic_version"), [("1",)])
        self.assert_cached_data_preserved()

    def test_unversioned_cache_applies_future_migrations(self):
        self.seed_current_cache()
        self.assert_future_upgrade()

    def test_versioned_cache_applies_future_migrations(self):
        self.seed_current_cache()
        self.run_db_init()
        self.assert_future_upgrade()

    def test_fresh_cache_uses_current_schema_without_replaying_migrations(self):
        self.add_future_revision()
        self.run_db_init()
        self.assertEqual(self.query("SELECT version_num FROM alembic_version"), [("2",)])
        self.assertEqual(self.query("SELECT migration_marker FROM issues_query"), [])
        self.assertEqual(
            self.query("SELECT indisvalid FROM pg_index WHERE indexrelid = 'issues_query_repo_id_idx'::regclass"),
            [(True,)],
        )

    def test_cli_generates_numeric_revisions_outside_cache_manager(self):
        self.run_db_init()
        for args in (("-m", "second"), ("--rev-id", "10", "-m", "explicit"), ("-m", "next")):
            argv = ["alembic", "-c", str(self.config), "revision", *args]
            self.run_python(f"import runpy; sys.argv = {argv!r}; runpy.run_module('alembic', run_name='__main__')")
        scripts = ScriptDirectory.from_config(Config(str(self.config)))
        self.assertEqual(
            [(revision.revision, revision.down_revision) for revision in scripts.walk_revisions()],
            [("11", "10"), ("10", "2"), ("2", "1"), ("1", None)],
        )


if __name__ == "__main__":
    unittest.main()
