"""Alembic environment for the cache schema.

Connects with cx_common's CACHE_* settings, so migrations target the app's
cache database. No ORM metadata: migrations are hand-written raw SQL.
"""

import os
import sys

from alembic import context
from sqlalchemy import URL, create_engine, pool

# Make cx_common (one directory up) importable from the CLI and from db_init.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cx_common import env_dbname, env_host, env_password, env_port, env_user

# Pass the URL object directly; setting it in Alembic's config breaks on '%' in passwords.
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
