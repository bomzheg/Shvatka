"""add players

Revision ID: 555d635df99f
Revises: 56df5c6b0df6
Create Date: 2022-07-18 22:16:46.815679

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "555d635df99f"
down_revision = "56df5c6b0df6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "players",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("can_be_author", sa.Boolean(), server_default="f", nullable=False),
        sa.Column("promoted_by_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["promoted_by_id"],
            ["players.id"],
        ),
        sa.UniqueConstraint("user_id"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("players")
