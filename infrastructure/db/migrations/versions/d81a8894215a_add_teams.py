"""add teams

Revision ID: d81a8894215a
Revises: 50b4aa6c0252
Create Date: 2022-11-20 19:11:37.584428

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d81a8894215a"
down_revision = "50b4aa6c0252"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=True),
        sa.Column("captain_id", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["captain_id"],
            ["players.id"],
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chats.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )


def downgrade():
    op.drop_table("teams")
