"""add a partial index for looking up the active game

get_active_game backs CurrentGameProvider, the game services and the /active
route, so it runs constantly, and it filters on the three statuses a running
game passes through. A partial index on exactly that predicate holds only the
handful of rows that are not yet complete, so it stays tiny and costs almost
nothing to maintain: a game's status changes a few times in its whole life.

The predicate must stay in step with ACTIVE_STATUSES in
shvatka.core.models.enums.game_status. Postgres can only use the index for a
query whose own predicate it implies, so adding a status to that tuple without
a new migration silently stops the index from covering the query.

Revision ID: d6e8f4a2b1c9
Revises: c5d7e3f1a9b8
Create Date: 2026-08-07 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "d6e8f4a2b1c9"
down_revision = "c5d7e3f1a9b8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix__games__active_status",
        "games",
        ["status"],
        unique=False,
        postgresql_where=sa.text("status IN ('getting_waivers', 'started', 'finished')"),
    )


def downgrade():
    op.drop_index("ix__games__active_status", table_name="games")
