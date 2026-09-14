"""add labels column to issues_query

Adds the labels column to caches created before it (CREATE TABLE
IF NOT EXISTS never alters existing tables). Fresh caches get it from the
CREATE block and are stamped at head, so this only runs on existing caches.

Clears cached issues and their bookkeeping so they are re-collected with
labels instead of keeping NULLs.

Revision ID: 0001_add_labels
Revises:
Create Date: 2026-08-26
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_add_labels"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE issues_query ADD COLUMN IF NOT EXISTS labels text")
    op.execute("TRUNCATE TABLE issues_query")
    op.execute("DELETE FROM cache_bookkeeping WHERE cache_func = 'issues_query'")


def downgrade() -> None:
    op.execute("TRUNCATE TABLE issues_query")
    op.execute("DELETE FROM cache_bookkeeping WHERE cache_func = 'issues_query'")
    op.execute("ALTER TABLE issues_query DROP COLUMN IF EXISTS labels")
