"""added player username

Revision ID: d4ddc1efb2ff
Revises: 4cfd8c9cf4f0
Create Date: 2026-05-03 11:56:33.447312

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4ddc1efb2ff'
down_revision = '4cfd8c9cf4f0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('players', sa.Column('username', sa.String(), nullable=True))
    op.create_unique_constraint(op.f('uq__players__username'), 'players', ['username'])
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
    op.drop_constraint(op.f('uq__players__username'), 'players', type_='unique')
    op.drop_column('players', 'username')
