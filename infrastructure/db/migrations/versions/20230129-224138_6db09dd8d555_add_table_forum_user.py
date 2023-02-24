"""add table forum_user

Revision ID: 6db09dd8d555
Revises: bc669f861ca9
Create Date: 2023-01-29 22:41:38.270852

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6db09dd8d555"
down_revision = "bc669f861ca9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "forum_users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("forum_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("registered", sa.Date(), nullable=False),
        sa.Column("player_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["player_id"], ["players.id"], name=op.f("forum_users_player_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__forum_users")),
        sa.UniqueConstraint("forum_id", name=op.f("uq__forum_users__forum_id")),
        sa.UniqueConstraint("player_id", name=op.f("uq__forum_users__player_id")),
    )


def downgrade():
    op.drop_table("forum_users")
