"""add game release

Revision ID: b7c2d4e6f8a1
Revises: d6e8f4a2b1c9
Create Date: 2026-08-07 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b7c2d4e6f8a1"
down_revision = "d6e8f4a2b1c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("games", sa.Column("release", postgresql.JSONB(), nullable=True))
    op.add_column("games", sa.Column("release_post", postgresql.JSONB(), nullable=True))


def downgrade():
    op.drop_column("games", "release_post")
    op.drop_column("games", "release")
