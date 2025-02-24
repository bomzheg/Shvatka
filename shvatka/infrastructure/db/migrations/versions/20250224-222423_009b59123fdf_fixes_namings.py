"""fixes namings

Revision ID: 009b59123fdf
Revises: 1659768228ec
Create Date: 2025-02-24 22:24:23.158449

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from shvatka.infrastructure.db.models.level import ScenarioField

# revision identifiers, used by Alembic.
revision = "009b59123fdf"
down_revision = "1659768228ec"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "forum_teams", "name", existing_type=sa.TEXT(), type_=sa.String(), existing_nullable=False
    )
    op.alter_column(
        "forum_teams", "url", existing_type=sa.TEXT(), type_=sa.String(), nullable=False
    )
    op.create_unique_constraint(op.f("uq__forum_teams__forum_id"), "forum_teams", ["forum_id"])
    op.alter_column(
        "forum_users", "name", existing_type=sa.TEXT(), type_=sa.String(), existing_nullable=False
    )
    op.alter_column(
        "forum_users", "url", existing_type=sa.TEXT(), type_=sa.String(), existing_nullable=True
    )
    op.alter_column("forum_users", "player_id", existing_type=sa.BIGINT(), nullable=False)
    op.alter_column(
        "games", "name", existing_type=sa.TEXT(), type_=sa.String(), existing_nullable=False
    )
    op.alter_column("games", "manage_token", existing_type=sa.TEXT(), nullable=False)
    op.alter_column(
        "levels",
        "scenario",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        type_=ScenarioField(astext_type=sa.Text()),
        nullable=False,
    )
    op.alter_column("levels_times", "level_number", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column(
        "team_players", "role", existing_type=sa.TEXT(), type_=sa.String(), nullable=False
    )
    op.alter_column(
        "team_players", "emoji", existing_type=sa.TEXT(), type_=sa.String(), existing_nullable=True
    )
    op.alter_column(
        "teams", "name", existing_type=sa.TEXT(), type_=sa.String(), existing_nullable=False
    )
    op.alter_column(
        "teams", "description", existing_type=sa.TEXT(), type_=sa.String(), existing_nullable=True
    )
    op.alter_column(
        "waivers", "role", existing_type=sa.TEXT(), type_=sa.String(), existing_nullable=True
    )


def downgrade():
    op.alter_column(
        "waivers", "role", existing_type=sa.String(), type_=sa.TEXT(), existing_nullable=True
    )
    op.alter_column(
        "teams", "description", existing_type=sa.String(), type_=sa.TEXT(), existing_nullable=True
    )
    op.alter_column(
        "teams", "name", existing_type=sa.String(), type_=sa.TEXT(), existing_nullable=False
    )
    op.alter_column(
        "team_players", "emoji", existing_type=sa.String(), type_=sa.TEXT(), existing_nullable=True
    )
    op.alter_column(
        "team_players", "role", existing_type=sa.String(), type_=sa.TEXT(), nullable=True
    )
    op.alter_column("levels_times", "level_number", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column(
        "levels",
        "scenario",
        existing_type=ScenarioField(astext_type=sa.Text()),
        type_=postgresql.JSON(astext_type=sa.Text()),
        nullable=True,
    )
    op.alter_column("games", "manage_token", existing_type=sa.TEXT(), nullable=True)
    op.alter_column(
        "games", "name", existing_type=sa.String(), type_=sa.TEXT(), existing_nullable=False
    )
    op.alter_column("forum_users", "player_id", existing_type=sa.BIGINT(), nullable=True)
    op.alter_column(
        "forum_users", "url", existing_type=sa.String(), type_=sa.TEXT(), existing_nullable=True
    )
    op.alter_column(
        "forum_users", "name", existing_type=sa.String(), type_=sa.TEXT(), existing_nullable=False
    )
    op.drop_constraint(op.f("uq__forum_teams__forum_id"), "forum_teams", type_="unique")
    op.alter_column(
        "forum_teams", "url", existing_type=sa.String(), type_=sa.TEXT(), nullable=True
    )
    op.alter_column(
        "forum_teams", "name", existing_type=sa.String(), type_=sa.TEXT(), existing_nullable=False
    )
