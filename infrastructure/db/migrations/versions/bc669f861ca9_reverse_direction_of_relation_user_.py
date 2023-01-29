"""reverse direction of relation user-player

Revision ID: bc669f861ca9
Revises: 852f6bcc741f
Create Date: 2023-01-29 12:55:04.929330

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import select
from sqlalchemy import table, Column, Integer

# revision identifiers, used by Alembic.
revision = "bc669f861ca9"
down_revision = "852f6bcc741f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("player_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(op.f("users_player_id_fkey"), "users", "players", ["player_id"], ["id"])

    players = table("players", Column("id", Integer, primary_key=True), Column("user_id"))
    users = table("users", Column("id", Integer, primary_key=True), Column("player_id"))
    op.execute(
        users.update().values(
            player_id=(
                select(players.c.id)
                .where(players.c.user_id == users.c.id)
                .limit(1)
                .scalar_subquery()
            )
        )
    )
    op.create_unique_constraint(op.f("uq__users__player_id"), "users", ["player_id"])
    op.drop_constraint("uq__players__user_id", "players", type_="unique")
    op.drop_constraint("players_user_id_fkey", "players", type_="foreignkey")
    op.drop_column("players", "user_id")


def downgrade():
    op.add_column("players", sa.Column("user_id", sa.BIGINT(), autoincrement=False, nullable=True))
    op.create_foreign_key("players_user_id_fkey", "players", "users", ["user_id"], ["id"])
    op.create_unique_constraint("uq__players__user_id", "players", ["user_id"])
    players = table("players", Column("id", Integer, primary_key=True), Column("user_id"))
    users = table("users", Column("id", Integer, primary_key=True), Column("player_id"))
    op.execute(
        players.update().values(
            user_id=(
                select(users.c.id)
                .where(users.c.player_id == players.c.id)
                .limit(1)
                .scalar_subquery()
            )
        )
    )
    op.drop_constraint(op.f("users_player_id_fkey"), "users", type_="foreignkey")
    op.drop_constraint(op.f("uq__users__player_id"), "users", type_="unique")
    op.drop_column("users", "player_id")
