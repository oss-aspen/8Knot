"""
Connection Common file - accessing environment variables
"""

from __future__ import annotations

import os
import logging
import time
from contextlib import contextmanager

# credentials to access database from environment
try:
    env_augur_user = os.environ["AUGUR_USERNAME"]
    env_augur_password = os.environ["AUGUR_PASSWORD"]
    env_augur_host = os.environ["AUGUR_HOST"]
    env_augur_port = os.environ["AUGUR_PORT"]
    env_augur_database = os.environ["AUGUR_DATABASE"]
    env_augur_schema = os.environ["AUGUR_SCHEMA"]
except KeyError as ke:
    logging.critical(f"AUGUR: Database credentials incomplete: {ke}")
    raise KeyError(ke)

# credentials to access application cache from environment
env_dbname = os.getenv("CACHE_DB_NAME", "augur_cache")
# TODO: define best default for openshift and docker compose
# env_host = os.getenv("CACHE_HOST", "eightknot-postgres-cache")
env_host = os.getenv("CACHE_HOST", "postgres-cache")
env_user = os.getenv("CACHE_USER", "postgres")
env_password = os.getenv("POSTGRES_PASSWORD", "password")
env_port = os.getenv("CACHE_PORT", "5432")
env_schema = os.getenv("CACHE_SCHEMA", "augur_data")


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


@contextmanager
def cache_connection():
    """Yield a psycopg2 connection to the cache DB, always closed on exit.

    Used by the shareable-URL system so callbacks never leak connections
    on the error paths. psycopg2 is imported lazily to keep this module
    import-light for code paths that only need the connection strings.
    """
    import psycopg2 as pg

    conn = pg.connect(cache_cx_string)
    try:
        yield conn
    finally:
        conn.close()
