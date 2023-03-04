"""add organizer

Revision ID: f11592799e60
Revises: 5545f6193665
Create Date: 2022-11-20 19:34:57.485585

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f11592799e60"
down_revision = "5545f6193665"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organizers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.BigInteger(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("can_spy", sa.Boolean(), nullable=False, server_default="f"),
        sa.Column("can_see_log_keys", sa.Boolean(), nullable=False, server_default="f"),
        sa.Column("can_validate_waivers", sa.Boolean(), nullable=False, server_default="f"),
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default="f"),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["players.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "game_id"),
    )


def downgrade():
    op.drop_table("organizers")
