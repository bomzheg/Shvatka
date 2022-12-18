"""add waivers

Revision ID: c92afe138ac8
Revises: 2ab6d1eefd77
Create Date: 2022-11-20 19:38:06.286284

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c92afe138ac8'
down_revision = '2ab6d1eefd77'
branch_labels = None
depends_on = None


waiver_status = sa.Enum(
    'yes', 'no', 'think', 'revoked', 'not_allowed', name='played',
)


def upgrade():
    op.create_table(
        'waivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('played', waiver_status, nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'team_id', 'player_id')
    )


def downgrade():
    op.drop_table('waivers')
    waiver_status.drop(op.get_bind(), checkfirst=False)
