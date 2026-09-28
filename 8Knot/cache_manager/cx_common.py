"""
Connection Common file - accessing environment variables
"""

import os
import time

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
