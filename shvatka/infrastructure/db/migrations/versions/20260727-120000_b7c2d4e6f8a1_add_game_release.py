"""add game release

Revision ID: b7c2d4e6f8a1
Revises: a3b5c1d9e7f6
Create Date: 2026-07-27 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b7c2d4e6f8a1"
down_revision = "a3b5c1d9e7f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("games", sa.Column("release", postgresql.JSONB(), nullable=True))
    op.add_column("games", sa.Column("release_post", postgresql.JSONB(), nullable=True))


def downgrade():
    op.drop_column("games", "release_post")
    op.drop_column("games", "release")
