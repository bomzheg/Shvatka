"""added column level_time_id to event log

Revision ID: 4cfd8c9cf4f0
Revises: d7e9e75ff5a8
Create Date: 2026-04-30 22:38:29.207195

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "4cfd8c9cf4f0"
down_revision = "d7e9e75ff5a8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("event_log", sa.Column("level_time_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        op.f("event_log_level_time_id_fkey"),
        "event_log",
        "levels_times",
        ["level_time_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(op.f("event_log_level_time_id_fkey"), "event_log", type_="foreignkey")
    op.drop_column("event_log", "level_time_id")
