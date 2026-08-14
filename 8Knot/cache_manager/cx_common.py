"""
Connection Common file - accessing environment variables
"""

import os
import logging
import time

# credentials to access database from environment
try:
    env_augur_user = os.environ["AUGUR_USERNAME"]
    env_augur_password = os.environ["AUGUR_PASSWORD"]
    env_augur_host = os.environ["AUGUR_HOST"]
    env_augur_port = os.environ["AUGUR_PORT"]
    env_augur_database = os.environ["AUGUR_DATABASE"]
except KeyError as ke:
    logging.critical(f"AUGUR: Database credentials incomplete: {ke}")
    raise KeyError(ke)

env_augur_schema = os.getenv("AUGUR_SCHEMA", "data,augur_data")

# credentials to access application cache from environment
env_dbname = os.getenv("CACHE_DB_NAME", "augur_cache")
# TODO: define best default for openshift and docker compose
# env_host = os.getenv("CACHE_HOST", "eightknot-postgres-cache")
env_host = os.getenv("CACHE_HOST", "postgres-cache")
env_user = os.getenv("CACHE_USER", "postgres")
env_password = os.getenv("POSTGRES_PASSWORD", "password")
env_port = os.getenv("CACHE_PORT", "5432")
env_schema = os.getenv("CACHE_SCHEMA", "data,augur_data")


# purely initial startup string
# psycopg2 connection string for cache pg instance, initialization only
init_cx_string = "dbname={} user={} password={} host={} port={}".format(
    "postgres", env_user, env_password, env_host, env_port
)

# psycopg2 connection string for cache pg instance
cache_cx_string = "dbname={} user={} password={} host={} port={}".format(
    env_dbname, env_user, env_password, env_host, env_port
)

# psycopg2 connection string for augur db
db_cx_string = "dbname={} user={} password={} host={} port={}".format(
    env_augur_database,
    env_augur_user,
    env_augur_password,
    env_augur_host,
    env_augur_port,
)

# how long a single statement may run against augur before the server aborts it.
# worker queries have to finish inside celery's soft time limit (540s), otherwise
# celery kills the worker and the query is orphaned on the augur server.
env_augur_statement_timeout_ms = os.getenv("AUGUR_STATEMENT_TIMEOUT_MS", "500000")

# the app-server's searchbar query legitimately takes much longer than a worker
# query, so it gets its own ceiling.
env_augur_engine_statement_timeout_ms = os.getenv("AUGUR_ENGINE_STATEMENT_TIMEOUT_MS", "1800000")

# how long a session may sit inside an open transaction before augur terminates it.
# a worker killed between fetches leaves its transaction open, so this is what
# reclaims the server-side cursor when 8Knot is shut down.
env_augur_idle_tx_timeout_ms = os.getenv("AUGUR_IDLE_TX_TIMEOUT_MS", "120000")


def augur_cx_options(statement_timeout_ms: str) -> str:
    """libpq 'options' for a connection to the augur db.

    Postgres won't stop working on our behalf just because we've disappeared: it
    doesn't check the client socket while it's busy in a query, so a query outlives
    the 8Knot instance that asked for it. These settings make the augur server
    responsible for cleaning up after us.

    tcp_keepalives_* apply to the server's end of the socket, so augur notices a
    container that no longer exists in ~90s rather than the OS default of 2 hours.
    """
    return " ".join(
        [
            f"-c search_path={env_augur_schema}",
            f"-c statement_timeout={statement_timeout_ms}",
            f"-c idle_in_transaction_session_timeout={env_augur_idle_tx_timeout_ms}",
            "-c tcp_keepalives_idle=60",
            "-c tcp_keepalives_interval=10",
            "-c tcp_keepalives_count=3",
        ]
    )
