"""add event-log

Revision ID: d6b4cb3976ab
Revises: 158d74e7d4cd
Create Date: 2026-02-03 09:09:13.009769

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "d6b4cb3976ab"
down_revision = "158d74e7d4cd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column(
            "at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("effects", JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], name=op.f("event_log_game_id_fkey")),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("event_log_team_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__event_log")),
    )
    op.add_column("log_keys", sa.Column("event_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("log_keys_event_id_fkey"), "log_keys", "event_log", ["event_id"], ["id"]
    )


def downgrade():
    op.drop_constraint(op.f("log_keys_event_id_fkey"), "log_keys", type_="foreignkey")
    op.drop_column("log_keys", "event_id")
    op.drop_table("event_log")
