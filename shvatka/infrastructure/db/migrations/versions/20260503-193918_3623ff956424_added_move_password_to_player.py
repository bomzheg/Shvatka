"""added move password to player

Revision ID: 3623ff956424
Revises: d4ddc1efb2ff
Create Date: 2026-05-03 19:39:18.837057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3623ff956424"
down_revision = "d4ddc1efb2ff"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("players", sa.Column("hashed_password", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE players p
        SET hashed_password=(select hashed_password
        from users u
        where u.player_id = p.id)
        """
    )


def downgrade():
    op.drop_column("players", "hashed_password")
