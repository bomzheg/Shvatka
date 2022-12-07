"""add achievements table

Revision ID: 51e122b5e734
Revises: c92afe138ac8
Create Date: 2022-12-07 08:47:31.142315

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '51e122b5e734'
down_revision = 'c92afe138ac8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'achievements',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.Enum('achievement', name='achievement', native_enum=False, length=256), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('first', sa.Boolean, server_default="f", nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('achievements')
