"""Record the current cache schema as the baseline for future migrations.

The CREATE blocks in db_init.py define this schema, including issues_query.labels.
Adopting versioning leaves existing tables and cached data intact; schemas older
than this baseline are not upgraded.

Revision ID: 1
Revises:
"""

revision = "1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    # Removing the baseline stamp must not remove pre-existing cache tables.
    pass
