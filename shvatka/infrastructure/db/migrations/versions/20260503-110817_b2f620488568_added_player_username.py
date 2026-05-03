"""added player username

Revision ID: b2f620488568
Revises: 4cfd8c9cf4f0
Create Date: 2026-05-03 11:08:17.268762

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2f620488568'
down_revision = '4cfd8c9cf4f0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('players', sa.Column('username', sa.String(), nullable=True))
    op.execute(
        """
        update players p
        set username = coalesce(
            (select u.username from users u where u.player_id = p.id),
            (select fu.name from forum_users fu where fu.player_id = p.id),
            'id' || p.id
        );
        """
    )


def downgrade():
    op.drop_column('players', 'username')
