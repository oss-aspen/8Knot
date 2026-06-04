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

# --- Durable application datastore (share links, future user state) ----------
# DELIBERATELY SEPARATE from the cache above. The cache DB is disposable: it is
# rebuilt from Augur and is reset on a schedule (UNLOGGED tables, see db_init
# and issue #1070). Share links must OUTLIVE those resets, so they live on their
# own Postgres instance ("postgres-app") with its own persistent volume that the
# cache-reset process never touches. Defaults reuse the cache credentials so a
# local stack works with no extra config; only the host/db differ.
env_app_dbname = os.getenv("APP_DB_NAME", "eightknot_app")
env_app_host = os.getenv("APP_DB_HOST", "postgres-app")
env_app_user = os.getenv("APP_DB_USER", env_user)
env_app_password = os.getenv("APP_DB_PASSWORD", env_password)
env_app_port = os.getenv("APP_DB_PORT", "5432")

# connect to the server's default db to create the app db on first boot
share_init_cx_string = "dbname={} user={} password={} host={} port={}".format(
    "postgres", env_app_user, env_app_password, env_app_host, env_app_port
)

# connect to the durable app db itself
share_cx_string = "dbname={} user={} password={} host={} port={}".format(
    env_app_dbname, env_app_user, env_app_password, env_app_host, env_app_port
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


@contextmanager
def share_connection():
    """Yield a psycopg2 connection to the DURABLE app DB (share links).

    Separate from cache_connection() on purpose: share links must survive cache
    resets, so they live in their own database/instance (see share_cx_string).
    """
    import psycopg2 as pg

    conn = pg.connect(share_cx_string)
    try:
        yield conn
    finally:
        conn.close()
