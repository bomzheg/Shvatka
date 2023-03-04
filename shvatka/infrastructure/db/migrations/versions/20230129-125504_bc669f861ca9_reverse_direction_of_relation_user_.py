"""reverse direction of relation user-player

Revision ID: bc669f861ca9
Revises: 852f6bcc741f
Create Date: 2023-01-29 12:55:04.929330

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bc669f861ca9"
down_revision = "852f6bcc741f"
branch_labels = None
depends_on = None

players = sa.table("players", sa.Column("id", sa.Integer, primary_key=True), sa.Column("user_id"))
users = sa.table("users", sa.Column("id", sa.Integer, primary_key=True), sa.Column("player_id"))


def upgrade():
    op.add_column("users", sa.Column("player_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(op.f("users_player_id_fkey"), "users", "players", ["player_id"], ["id"])
    op.execute(
        users.update().values(
            player_id=(
                sa.select(players.c.id)
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
    op.execute(
        players.update().values(
            user_id=(
                sa.select(users.c.id)
                .where(users.c.player_id == players.c.id)
                .limit(1)
                .scalar_subquery()
            )
        )
    )
    op.drop_constraint(op.f("users_player_id_fkey"), "users", type_="foreignkey")
    op.drop_constraint(op.f("uq__users__player_id"), "users", type_="unique")
    op.drop_column("users", "player_id")
