"""add games

Revision ID: aeac6812b5c0
Revises: d81a8894215a
Create Date: 2022-11-20 19:12:42.614267

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "aeac6812b5c0"
down_revision = "d81a8894215a"
branch_labels = None
depends_on = None

game_status = sa.Enum(
    "underconstruction",
    "ready",
    "getting_waivers",
    "started",
    "finished",
    "complete",
    name="game_status",
)


def upgrade():
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("status", game_status, server_default="underconstruction", nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_channel_id", sa.BigInteger(), nullable=True),
        sa.Column("manage_token", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["players.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("author_id", "name"),
        sa.UniqueConstraint("name"),
    )


def downgrade():
    op.drop_table("games")
    game_status.drop(op.get_bind(), checkfirst=False)
