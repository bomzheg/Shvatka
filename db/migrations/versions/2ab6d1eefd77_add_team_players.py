"""add team_players

Revision ID: 2ab6d1eefd77
Revises: f11592799e60
Create Date: 2022-11-20 19:37:10.291248

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2ab6d1eefd77'
down_revision = 'f11592799e60'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'team_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('date_joined', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('emoji', sa.Text(), nullable=True),
        sa.Column('date_left', sa.DateTime(timezone=True), nullable=True),
        sa.Column('can_manage_waivers', sa.Boolean(), nullable=False, server_default="f"),
        sa.Column('can_manage_players', sa.Boolean(), nullable=False, server_default="f"),
        sa.Column('can_change_team_name', sa.Boolean(), nullable=False, server_default="f"),
        sa.Column('can_add_players', sa.Boolean(), nullable=False, server_default="f"),
        sa.Column('can_remove_players', sa.Boolean(), nullable=False, server_default="f"),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('team_players')
