"""add emails table

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-07-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e5f6a1b2c3d4"
down_revision = "d4e5f6a1b2c3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "emails",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default="f", nullable=False),
        sa.Column("player_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["players.id"],
            name=op.f("emails_player_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__emails")),
        sa.UniqueConstraint("email", name=op.f("uq__emails__email")),
        sa.UniqueConstraint("player_id", name=op.f("uq__emails__player_id")),
    )


def downgrade():
    op.drop_table("emails")
