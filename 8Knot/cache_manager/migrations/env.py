"""Alembic environment for the Postgres cache schema.

The connection URL is built from the same CACHE_* environment variables
that cx_common uses, so Alembic and the running app always target the
same cache database. We deliberately do NOT use autogenerate / ORM
metadata: the cache schema is defined with raw SQL (see db_init.py), so
migrations are hand-written raw SQL too, and target_metadata stays None.
"""

import os
import sys

from alembic import context
from sqlalchemy import URL, create_engine, pool

# cx_common lives one directory up (8Knot/cache_manager); make it importable
# whether Alembic is invoked via the CLI from migrations/ or programmatically.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cx_common import env_dbname, env_host, env_password, env_port, env_user

# Keep credentials as a URL object. Rendering into Alembic's Config would
# make percent-encoded passwords subject to ConfigParser interpolation.
database_url = URL.create(
    "postgresql+psycopg2",
    username=env_user,
    password=env_password,
    host=env_host,
    port=int(env_port),
    database=env_dbname,
)

# No ORM models in this project, so no autogenerate support.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
