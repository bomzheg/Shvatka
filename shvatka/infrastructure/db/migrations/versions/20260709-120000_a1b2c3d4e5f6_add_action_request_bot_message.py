"""add action request bot message ids

Revision ID: a1b2c3d4e5f6
Revises: f6a1b2c3d4e5
Create Date: 2026-07-09 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f6a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "action_requests",
        sa.Column("bot_messages", sa.JSON(), server_default="[]", nullable=False),
    )


def downgrade():
    op.drop_column("action_requests", "bot_messages")
