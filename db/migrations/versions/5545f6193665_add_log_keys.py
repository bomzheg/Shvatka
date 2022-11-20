"""add log_keys

Revision ID: 5545f6193665
Revises: 1e1b2716e49b
Create Date: 2022-11-20 19:33:07.338946

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '5545f6193665'
down_revision = '1e1b2716e49b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'log_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('level_number', sa.Integer(), nullable=False),
        sa.Column(
            'enter_time', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column('key_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('log_keys')
