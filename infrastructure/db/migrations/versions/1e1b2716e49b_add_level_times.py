"""add level_times

Revision ID: 1e1b2716e49b
Revises: f5915dae5735
Create Date: 2022-11-20 19:31:51.632976

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1e1b2716e49b'
down_revision = 'f5915dae5735'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'levels_times',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('level_number', sa.Integer(), nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'team_id', 'level_number')
    )


def downgrade():
    op.drop_table('levels_times')
