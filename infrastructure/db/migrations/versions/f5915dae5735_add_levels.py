"""add levels

Revision ID: f5915dae5735
Revises: aeac6812b5c0
Create Date: 2022-11-20 19:25:56.047910

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f5915dae5735'
down_revision = 'aeac6812b5c0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name_id', sa.Text(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=False),
        sa.Column('number_in_game', sa.Integer(), nullable=True),
        sa.Column('scenario', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('author_id', 'name_id')
    )


def downgrade():
    op.drop_table('levels')
