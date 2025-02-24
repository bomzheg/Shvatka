"""allow level times cycles

Revision ID: 149de95bb84e
Revises: 009b59123fdf
Create Date: 2025-02-24 22:31:03.293138

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "149de95bb84e"
down_revision = "009b59123fdf"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq__levels_times__game_id", "levels_times", type_="unique")


def downgrade():
    op.create_unique_constraint(
        "uq__levels_times__game_id", "levels_times", ["game_id", "team_id", "level_number"]
    )
