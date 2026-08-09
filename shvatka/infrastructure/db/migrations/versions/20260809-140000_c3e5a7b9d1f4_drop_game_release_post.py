"""drop game release post

Revision ID: c3e5a7b9d1f4
Revises: e1a3c5d7b9f2
Create Date: 2026-08-09 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c3e5a7b9d1f4"
down_revision = "e1a3c5d7b9f2"
branch_labels = None
depends_on = None


def upgrade():
    # where a release stands in the channel is the announcing view's own
    # bookkeeping, kept by the bot beside its pinned messages — the game has
    # no business holding chat and message ids
    op.drop_column("games", "release_post")


def downgrade():
    op.add_column("games", sa.Column("release_post", postgresql.JSONB(), nullable=True))
