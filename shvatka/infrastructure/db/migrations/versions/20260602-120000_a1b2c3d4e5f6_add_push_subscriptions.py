"""add push subscriptions

Revision ID: a1b2c3d4e5f6
Revises: 4eac69a6875d
Create Date: 2026-06-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "4eac69a6875d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("player_id", sa.BigInteger(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="t", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["player_id"], ["players.id"], name=op.f("push_subscriptions_player_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__push_subscriptions")),
        sa.UniqueConstraint("endpoint", name=op.f("uq__push_subscriptions__endpoint")),
    )
    op.create_index(
        op.f("ix__push_subscriptions_player_id"),
        "push_subscriptions",
        ["player_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix__push_subscriptions_player_id"), table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
