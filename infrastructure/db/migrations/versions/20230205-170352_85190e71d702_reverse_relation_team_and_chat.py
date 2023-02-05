"""reverse relation team and chat

Revision ID: 85190e71d702
Revises: 6db09dd8d555
Create Date: 2023-02-05 17:03:52.983330

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "85190e71d702"
down_revision = "6db09dd8d555"
branch_labels = None
depends_on = None

teams = sa.table("teams", sa.Column("id", sa.Integer, primary_key=True), sa.Column("chat_id"))
chats = sa.table("chats", sa.Column("id", sa.Integer, primary_key=True), sa.Column("team_id"))


def upgrade():
    op.add_column("chats", sa.Column("team_id", sa.Integer(), nullable=True))
    op.create_unique_constraint(op.f("uq__chats__team_id"), "chats", ["team_id"])
    op.create_foreign_key(op.f("chats_team_id_fkey"), "chats", "teams", ["team_id"], ["id"])
    op.execute(
        chats.update().values(
            team_id=(
                sa.select(teams.c.id)
                .where(teams.c.chat_id == chats.c.id)
                .limit(1)
                .scalar_subquery()
            )
        )
    )
    op.drop_constraint("uq__teams__chat_id", "teams", type_="unique")
    op.drop_constraint("teams_chat_id_fkey", "teams", type_="foreignkey")
    op.drop_column("teams", "chat_id")


def downgrade():
    op.add_column("teams", sa.Column("chat_id", sa.BIGINT(), autoincrement=False, nullable=True))
    op.create_foreign_key("teams_chat_id_fkey", "teams", "chats", ["chat_id"], ["id"])
    op.create_unique_constraint("uq__teams__chat_id", "teams", ["chat_id"])
    op.execute(
        teams.update().values(
            chat_id=(
                sa.select(chats.c.id)
                .where(chats.c.team_id == teams.c.id)
                .limit(1)
                .scalar_subquery()
            )
        )
    )
    op.drop_constraint(op.f("chats_team_id_fkey"), "chats", type_="foreignkey")
    op.drop_constraint(op.f("uq__chats__team_id"), "chats", type_="unique")
    op.drop_column("chats", "team_id")
