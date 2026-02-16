"""add timer table

Revision ID: 7e98407ed5e8
Revises: d6b4cb3976ab
Create Date: 2026-02-03 09:14:55.623508

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7e98407ed5e8"
down_revision = "d6b4cb3976ab"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "timers_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("level_time_id", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["event_id"], ["event_log.id"], name=op.f("timers_log_event_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["level_time_id"], ["levels_times.id"], name=op.f("timers_log_level_time_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__timers_log")),
    )


def downgrade():
    op.drop_table("timers_log")
