"""add view_scenario to organizer

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-06-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a1b2"
down_revision = "b2c3d4e5f6a1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organizers",
        sa.Column("view_scenario", sa.Boolean(), nullable=False, server_default="f"),
    )


def downgrade():
    op.drop_column("organizers", "view_scenario")
