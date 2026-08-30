"""add labels column to issues_query

Backfills the `labels` column that PR #1189 added to the issues_query
CREATE block. CREATE TABLE IF NOT EXISTS never alters a table that
already exists, so caches created before #1189 are missing the column
(which is why the issues visualizations guard with
`if "labels" not in df.columns`). This migration adds it to those caches.

Fresh caches already get the column from db_init's CREATE block and are
stamped straight to head, so this migration only runs against a
pre-existing cache. Existing issue rows must be invalidated because their
new labels value is NULL, while cache_bookkeeping would otherwise prevent
those repositories from being collected again.

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
