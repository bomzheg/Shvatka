"""add table users

Revision ID: 4e570bc94610
Revises:
Create Date: 2022-02-02 23:37:50.228477

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4e570bc94610'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=True),
        sa.Column('first_name', sa.Text(), nullable=True),
        sa.Column('last_name', sa.Text(), nullable=True),
        sa.Column('username', sa.Text(), nullable=True),
        sa.Column('is_bot', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tg_id'),
    )


def downgrade():
    op.drop_table('users')
