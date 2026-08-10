"""add game release banner

Revision ID: e1a3c5d7b9f2
Revises: b7c2d4e6f8a1
Create Date: 2026-08-08 09:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "e1a3c5d7b9f2"
down_revision = "b7c2d4e6f8a1"
branch_labels = None
depends_on = None


def upgrade():
    # the banner leads the release and is the only part shown above the site's
    # header, so it is read on its own rather than picked out of the body
    op.add_column("games", sa.Column("release_banner", postgresql.JSONB(), nullable=True))


def downgrade():
    op.drop_column("games", "release_banner")
