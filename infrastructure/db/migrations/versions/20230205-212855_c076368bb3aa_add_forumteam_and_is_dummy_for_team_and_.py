"""add ForumTeam and is_dummy for team and player

Revision ID: c076368bb3aa
Revises: 85190e71d702
Create Date: 2023-02-05 21:28:55.272704

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c076368bb3aa"
down_revision = "85190e71d702"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "forum_teams",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name=op.f("forum_teams_team_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__forum_teams")),
        sa.UniqueConstraint("team_id", name=op.f("uq__forum_teams__team_id")),
    )

    op.add_column(
        "players", sa.Column("is_dummy", sa.Boolean(), server_default="f", nullable=False)
    )
    op.add_column("teams", sa.Column("is_dummy", sa.Boolean(), server_default="f", nullable=False))


def downgrade():
    op.drop_column("teams", "is_dummy")
    op.drop_column("players", "is_dummy")
    op.drop_table("forum_teams")
