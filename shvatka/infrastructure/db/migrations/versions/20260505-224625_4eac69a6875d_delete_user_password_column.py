"""delete user password column

Revision ID: 4eac69a6875d
Revises: 3623ff956424
Create Date: 2026-05-05 22:46:25.458262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4eac69a6875d"
down_revision = "3623ff956424"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("users", "hashed_password")


def downgrade():
    op.add_column(
        "users", sa.Column("hashed_password", sa.TEXT(), autoincrement=False, nullable=True)
    )
    op.execute(
        """
        UPDATE users u
        SET hashed_password=(select hashed_password
        from players p
        where u.player_id = p.id)
        """
    )
