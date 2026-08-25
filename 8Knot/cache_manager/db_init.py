"""
NOTES ABOUT THIS FILE:

This file uses raw SQL to create tables in Postgres.
It's typically easiest and best-practice to use a db migration
tool instead of doing error-prone manual administration like this.

However, using sqlalchemy and alembic (Python db migration stack)
would be a bit of a steep learning curve for people who just want to
create a table in the cache. Most people who would be working on a
project like this will know enough SQL to read the existing table
definitions and create a new table as needed from those examples.

We don't use alembic here because this database is a disposable,
UNLOGGED cache: every table is rebuildable from CollectOSS and is already
lost on any unclean restart, the schema is a small fixed set of tables,
and there's no ORM - contributors work in raw SQL. Standing up alembic
would mean modeling all of that just to bootstrap an alembic_version
table, which isn't worth it for a throwaway cache. Instead, schema
changes to existing tables are handled on startup: idempotent ones run
unconditionally (see _ensure_repo_id_indexes below) and the rest are
numbered entries in MIGRATIONS, applied in order. We can adopt alembic
later if the schema outgrows this.
"""

"""
TABLE_CREATION_INSTRUCTIONS:

For data that we retrieve from Postgres to be cached, we need
to define the "schema" for the table where it will be stored.

Take a moment to look at the correspondence between the table
"commits_query" in this file and the SQL that we have the database
execute, defined in "queries/commits_query.py." Notice that each
of the columns referenced in the SELECT statement has a
corresponding column in the table schema defined below, with a
type that matches the datatype we expect to receive from Augur.

Note also that we use the table creation syntax:
CREATE UNLOGGED TABLE IF NOT EXISTS <name>

We configure the tables to be unlogged to maximize write-to speed.
We can always repopulate a table with minimal inconvenience if
the cache database is destroyed, so we don't need the durability
guarantees of a logged table.

We also only create a new table if a table of the same name
does not already exist. This initialization script ALWAYS runs
on app startup to make sure that the schema of the databse is
intact between application restarts.

CREATE IF NOT EXISTS cannot change a table that already exists.
Changes to existing tables fall into two categories:

(1) Safely re-appliable with an IF NOT EXISTS / IF EXISTS guard (e.g. a
    new index, like _ensure_repo_id_indexes() below). These don't need
    versioning - just add your own function and call it unconditionally
    on every boot, same as _create_application_tables().

(2) Not safely re-appliable (e.g. dropping/renaming a column, changing a
    type). These go in a numbered migration in MIGRATIONS below. On
    startup we compare cache_schema_version to the latest migration and
    apply anything missing. Existing caches with no version table are
    treated as version 0.

To add a new table to the cache, simply copy an existing table
creation block from those below. Given that you're creating a table
for a query in the 'queries/' folder, name the table the same name
as the query function. Name the columns of the table, and give their
types, and everything should work!

To make a non-re-appliable change to an existing table, add a function
to MIGRATIONS with the next integer version. Do not edit old
migration functions.

Here's a list of types that postgres defines:
https://www.postgresql.org/docs/current/datatype.html

Generally, 'int' is good for integers,
'float4' is good for normal floats,
'float8' is good for larger precision floats,
'text' is best for text strings.
    - why we aren't using 'varchar':
    https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_varchar.28n.29_by_default
"""

import logging
import sys
import os
import psycopg2 as pg
import redis
import time


def _env_int(var: str, default: int) -> int:
    """Parse an environment variable as an integer with safe fallback.

    Wraps int() conversion in a try/except so that misconfigured
    environment variables never crash the application on startup.

    Behavior:
        - Env var is unset or empty  -> returns *default*.
        - Env var is a valid integer -> returns int(value).
        - Env var is non-numeric (e.g. "ABCD") -> the string is truthy
          so int() is attempted, raises ValueError, which is caught;
          logs a warning so the misconfiguration is visible and falls
          back to *default*.

    Args:
        var:     Name of the environment variable.
        default: Value returned when the variable is absent, empty,
                 or cannot be parsed as an integer.

    Returns:
        The parsed integer, or *default* on any failure.
    """
    raw = os.getenv(var, "")
    try:
        return int(raw) if raw else default
    except ValueError:
        logging.warning(f"db_init: ignoring non-numeric {var}={raw!r}, using {default}")
        return default


# doesn't use relative import syntax "import .cx_common" because
# cx_common is a neighbor of script, thus is available in PYTHON_PATH
from cx_common import init_cx_string, cache_cx_string


def _connect_with_retry(connection_string, max_retries=5, retry_delay=3):
    """
    Attempt to connect to the database with retries.
    Args:
        connection_string: The connection string to use
        max_retries: Maximum number of retry attempts
        retry_delay: Seconds to wait between retries
    Returns:
        PostgreSQL connection object or None if failed after retries
    """
    retries = 0
    last_exception = None
    while retries < max_retries:
        try:
            logging.warning(f"Attempting database connection (attempt {retries+1}/{max_retries})...")
            conn = pg.connect(connection_string)
            logging.warning("Database connection established successfully!")
            return conn
        except Exception as e:
            last_exception = e
            retries += 1
            if retries < max_retries:
                logging.warning(f"Connection failed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logging.critical(f"Failed to connect after {max_retries} attempts: {e}")
    # If we reached here, all connection attempts failed
    raise last_exception


def _create_application_database() -> None:
    """
    On fresh application boot, Postgres is fresh, so
    database where we cache data from Augur isn't configured.

    This function creates the 'augur_cache' database, which will
    contain all of the tables where we'll cache data for visualization.
    """

    # Connect to the dbms at top-level
    # to instantiate application db
    # we'll always connect to root-level DB
    # with these creds so they don't need to be
    # parameterized.
    conn = _connect_with_retry(init_cx_string)

    # required so that we can create a database
    conn.autocommit = True

    # check if application db already exists
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'augur_cache'")
    exists = cur.fetchone()

    # create application db if it doesn't already exist
    if not exists:
        logging.warning("CREATING augur_cache DATABASE")
        cur.execute("CREATE DATABASE augur_cache")

    conn.commit()
    cur.close()
    conn.close()


def _create_application_tables() -> None:
    """
    Creates tables for cached data in 'augur_cache' database.

    Tables created:
        - commits
        - cache_bookkeeping
    """
    # TODO: timestamps being stored as strings- don't need to do that anymore.

    # connect to application database
    conn = _connect_with_retry(cache_cx_string)

    with conn.cursor() as cur:
        # create tables if they don't already exist.
        # TODO: id->repo_id, commits->commit_id
        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS commits_query(
                repo_id int,
                commit_hash text, -- this is the commit hash, so it's base64 hash.
                author_email text,
                author_date text,
                author_timestamp text,
                committer_timestamp text)
            """
        )
        logging.warning("CREATED commits TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS issues_query(
                repo_id bigint,
                repo_name text,
                issue bigint,
                issue_number bigint,
                gh_issue bigint,
                reporter_id text,
                issue_closer text,
                created_at text,
                closed_at text,
                labels text
            )
            """
        )
        logging.warning("CREATED issues TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS prs_query(
                repo_id int,
                repo_name text,
                pull_request_id int,
                pr_src_number int,
                cntrb_id text,
                created_at text,
                closed_at text,
                merged_at text,
                merger_cntrb_id text
            )
            """
        )
        logging.warning("CREATED prs TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS affiliation_query(
                cntrb_id text,
                created_at text,
                repo_id int,
                login text,
                action text,
                cntrb_company text,
                email_list text
            )
            """
        )
        logging.warning("CREATED affiliation_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS contributors_query(
                repo_id int,
                repo_name text,
                cntrb_id text,
                created_at text,
                login text,
                action text
            )
            """
        )
        logging.warning("CREATED contributors TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS issue_assignee_query(
                issue_id text,
                repo_id int,
                created_at text,
                closed_at text,
                assign_date text,
                assignment_action text,
                assignee text
            )
            """
        )
        logging.warning("CREATED issue_assignments TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS pr_assignee_query(
                pull_request_id int,
                repo_id int,
                created_at text,
                closed_at text,
                assign_date text,
                assignment_action text,
                assignee text
            )
            """
        )
        logging.warning("CREATED pr_assignments TABLE")

        # Codebase page tables - enabled for heatmap visualizations
        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS cntrb_per_file_query(
                repo_id int,
                file_path text,
                cntrb_ids text,
                reviewer_ids text
            )
            """
        )
        logging.warning("CREATED cntrb_per_file_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS pr_file_query(
                file_path text,
                pull_request int,
                repo_id int
            )
            """
        )
        logging.warning("CREATED pr_file_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS repo_files_query(
                repo_id int,
                repo_name text,
                repo_path text,
                rl_analysis_date text,
                file_path text,
                file_name text
            )
            """
        )
        logging.warning("CREATED repo_files_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS repo_languages_query(
                repo_id int,
                programming_language text,
                code_lines int,
                files int
            )
            """
        )
        logging.warning("CREATED repo_languages_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS package_version_query(
                repo_id int,
                name text,
                current_release_date text,
                latest_release_date text,
                libyear float4,
                dep_age text
            )
            """
        )
        logging.warning("CREATED package_version_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS repo_releases_query(
                repo_id int,
                release_name text,
                release_created_at text,
                release_published_at text,
                release_updated_at text
            )
            """
        )
        logging.warning("CREATED repo_releases_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS ossf_score_query(
                repo_id int,
                name text,
                score float4,
                data_collection_date timestamp
            )
            """
        )
        logging.warning("CREATED ossf_score_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS repo_info_query(
                repo_id int,
                issues_enabled text,
                fork_count int,
                watchers_count int,
                license text,
                stars_count int,
                code_of_conduct_file text,
                security_issue_file text,
                security_audit_file text,
                data_collection_date timestamp
            )
            """
        )
        logging.warning("CREATED repo_info_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS pr_response_query(
                pull_request_id int,
                repo_id int,
                cntrb_id text,
                msg_timestamp text,
                msg_cntrb_id text,
                pr_created_at text,
                pr_closed_at text
            )
            """
        )
        logging.warning("CREATED pr_response_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS cache_bookkeeping(
                cache_func text,
                repo_id int,
                ts_cached timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        logging.warning("CREATED cache_bookkeeping TABLE")

        # commit changes, all-or-nothing.
        conn.commit()

    logging.warning("ALL TABLES COMMITTED SUCCESSFULLY")


def _ensure_repo_id_indexes() -> None:
    """Ensure every cache table with a repo_id column has an index on it.

    retrieve_from_cache() and get_uncached() both filter on repo_id, and
    UNLOGGED tables don't auto-index, so a missing index means a full
    sequential scan (issue #1198 / PR #1158). Rather than hardcode the
    table list, we ask Postgres which tables currently have a repo_id
    column, so any table added later (via a new CREATE IF NOT EXISTS block
    above) gets indexed the next time this runs - nothing to remember to
    update here.

    CREATE INDEX IF NOT EXISTS is always safely re-appliable, so unlike a
    real schema migration (see MIGRATIONS below), this doesn't need to be
    gated by cache_schema_version - it just runs unconditionally on every
    boot, the same way _create_application_tables() does.

    cache_bookkeeping also has a repo_id column but is queried by
    (cache_func, repo_id) instead, so it's excluded here and given its own
    composite index.
    """
    conn = _connect_with_retry(cache_cx_string)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name FROM information_schema.columns
                WHERE table_schema = 'public' AND column_name = 'repo_id' AND table_name != 'cache_bookkeeping'
                """
            )
            tables = [row[0] for row in cur.fetchall()]
            for table in tables:
                cur.execute(f"CREATE INDEX IF NOT EXISTS {table}_repo_id_idx ON {table} (repo_id)")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS cache_bookkeeping_func_repo_idx ON cache_bookkeeping (cache_func, repo_id)"
            )
        conn.commit()
    finally:
        conn.close()
    logging.warning(f"db_init: ensured repo_id indexes ({len(tables)} tables)")


def _backfill_issues_query_columns() -> None:
    """Add columns introduced after issues_query was first created.

    PR #1189 added a `labels` column to the issues_query CREATE block, but
    CREATE TABLE IF NOT EXISTS never alters a table that already exists, so
    caches created before #1189 are missing it - which is why the issues
    visualizations currently guard with `if "labels" not in df.columns`.
    ADD COLUMN IF NOT EXISTS is idempotent, so like _ensure_repo_id_indexes
    this is a category-1 change that runs unconditionally rather than a
    numbered migration.
    """
    conn = _connect_with_retry(cache_cx_string)
    try:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE issues_query ADD COLUMN IF NOT EXISTS labels text")
        conn.commit()
    finally:
        conn.close()
    logging.warning("db_init: ensured issues_query.labels column")


# Integer versions, applied in order. Never edit a past entry; add a new one.
# Reserved for changes that can't be made safely re-appliable, like dropping
# or renaming a column. Changes that are safe as CREATE/INDEX IF NOT EXISTS
# forever (like _ensure_repo_id_indexes above) don't belong here - they
# should just run unconditionally on every boot instead.
MIGRATIONS = {}


def _apply_schema_migrations() -> None:
    """Bring an existing cache schema up to the latest version.

    Caches with no cache_schema_version table (today's production DBs)
    are version 0. Each pending migration runs, then we stamp that
    version in the same transaction. Failure rolls back and db_init
    exits non-zero so the init container retries.
    """
    conn = _connect_with_retry(cache_cx_string)
    latest = max(MIGRATIONS, default=0)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_schema_version (
                    version int PRIMARY KEY,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute("SELECT COALESCE(MAX(version), 0) FROM cache_schema_version")
            current = cur.fetchone()[0]
            logging.warning(f"db_init: cache schema version {current}, latest {latest}")

            for version in range(current + 1, latest + 1):
                logging.warning(f"db_init: applying cache schema migration {version}")
                MIGRATIONS[version](cur)
                cur.execute("INSERT INTO cache_schema_version (version) VALUES (%s)", (version,))

            conn.commit()
    finally:
        conn.close()
    logging.warning(f"db_init: cache schema at version {latest}")


def _flush_redis_broker() -> None:
    """
    Flush the Redis broker so it stays in sync with postgres-cache.

    postgres-cache uses UNLOGGED tables, so all cached data is lost on
    restart. If Redis still holds stale Celery task messages or results
    from a previous run, workers pick them up and poll for data that no
    longer exists, causing deadlocks. Flushing here guarantees a clean
    broker state every time the cache is (re)initialized.
    """
    broker_host = os.getenv("REDIS_SERVICE_HOST", "redis-broker")
    broker_port = _env_int("REDIS_SERVICE_PORT", 6379)
    broker_password = os.getenv("REDIS_PASSWORD", "")

    users_host = os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users")
    users_port = _env_int("REDIS_SERVICE_USERS_PORT", 6379)

    for name, host, port in [
        ("redis-broker", broker_host, broker_port),
        ("redis-users", users_host, users_port),
    ]:
        try:
            r = redis.StrictRedis(host=host, port=port, password=broker_password)
            r.flushall()
            logging.warning(f"db_init: FLUSHED {name} ({host}:{port})")
        except Exception as e:
            logging.warning(f"db_init: could not flush {name}: {e}")


def db_init() -> int:
    # Redis must be flushed every boot regardless of whether the Postgres
    # steps below succeed: leftover Celery broker tasks from a previous run
    # get picked up by new workers and hang trying to fetch cache rows/repos
    # that no longer exist. So its success/failure is tracked separately
    # from the Postgres steps rather than short-circuited by them.
    postgres_ok = True
    try:
        # don't need to check return values- errors propogate as exceptions,
        # which will halt init altogether.

        # create augur_cache db if it doesn't already exist.
        _create_application_database()

        # add tables to augur_cache db if they don't already exist.
        _create_application_tables()

        # index any table with a repo_id column - always, so new tables
        # stay covered automatically without any manual bookkeeping.
        _ensure_repo_id_indexes()

        # backfill columns added to existing tables after they were created.
        _backfill_issues_query_columns()

        # apply any versioned schema changes that aren't safely re-appliable.
        _apply_schema_migrations()

        logging.warning("db_init: POSTGRES CACHE SUCCESSFULLY INITIALIZED")

    except Exception as e:
        logging.critical(f"POSTGRES ERROR: {e}")
        postgres_ok = False

    # flush redis so broker state matches the postgres-cache, even if the
    # postgres steps above failed.
    _flush_redis_broker()

    return 0 if postgres_ok else 1


if __name__ == "__main__":
    sys.exit(db_init())
