"""add notifications and action_requests

Revision ID: f6a1b2c3d4e5
Revises: e5f6a1b2c3d4
Create Date: 2026-07-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f6a1b2c3d4e5"
down_revision = "e5f6a1b2c3d4"
branch_labels = None
depends_on = None


request_status = sa.Enum(
    "pending",
    "accepted",
    "declined",
    "cancelled",
    "expired",
    name="request_status",
)
notification_severity = sa.Enum(
    "low",
    "normal",
    "important",
    name="notification_severity",
)


def upgrade():
    op.create_table(
        "action_requests",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("status", request_status, server_default="pending", nullable=False),
        sa.Column("initiator_id", sa.BigInteger(), nullable=False),
        sa.Column("target_player_id", sa.BigInteger(), nullable=True),
        sa.Column("team_id", sa.BigInteger(), nullable=True),
        sa.Column("game_id", sa.BigInteger(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("responder_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["initiator_id"],
            ["players.id"],
            name=op.f("action_requests_initiator_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_player_id"],
            ["players.id"],
            name=op.f("action_requests_target_player_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name=op.f("action_requests_team_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name=op.f("action_requests_game_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["responder_id"],
            ["players.id"],
            name=op.f("action_requests_responder_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__action_requests")),
    )
    op.create_index(
        op.f("ix__action_requests_target_player_id"),
        "action_requests",
        ["target_player_id"],
        unique=False,
    )
    op.create_index(
        "ix__action_requests_pending_team",
        "action_requests",
        ["team_id"],
        unique=False,
        postgresql_where=sa.text("status = 'pending'"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("recipient_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("severity", notification_severity, server_default="normal", nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("request_id", sa.BigInteger(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["players.id"],
            name=op.f("notifications_recipient_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["players.id"],
            name=op.f("notifications_actor_id_fkey"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["action_requests.id"],
            name=op.f("notifications_request_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__notifications")),
    )
    op.create_index(
        op.f("ix__notifications_recipient_id"),
        "notifications",
        ["recipient_id"],
        unique=False,
    )
    op.create_index(
        "ix__notifications_recipient_created",
        "notifications",
        ["recipient_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "ix__notifications_unread",
        "notifications",
        ["recipient_id"],
        unique=False,
        postgresql_where=sa.text("read_at IS NULL"),
    )


def downgrade():
    op.drop_index("ix__notifications_unread", table_name="notifications")
    op.drop_index("ix__notifications_recipient_created", table_name="notifications")
    op.drop_index(op.f("ix__notifications_recipient_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix__action_requests_pending_team", table_name="action_requests")
    op.drop_index(op.f("ix__action_requests_target_player_id"), table_name="action_requests")
    op.drop_table("action_requests")
    notification_severity.drop(op.get_bind(), checkfirst=False)
    request_status.drop(op.get_bind(), checkfirst=False)
