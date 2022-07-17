"""add table chats

Revision ID: 56df5c6b0df6
Revises: 4e570bc94610
Create Date: 2022-02-03 21:10:34.415987

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.

revision = '56df5c6b0df6'
down_revision = '4e570bc94610'
branch_labels = None
depends_on = None

chat_type = postgresql.ENUM('private', 'channel', 'group', 'supergroup',
                            name='chattype', create_type=False)


def upgrade():
    chat_type.create(op.get_bind())
    op.create_table(
        'chats',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=True),
        sa.Column('type', chat_type, nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('username', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tg_id')
    )


def downgrade():
    op.drop_table('chats')
    chat_type.drop(op.get_bind())
