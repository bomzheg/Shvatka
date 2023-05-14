"""use bigint for published channel id

Revision ID: fb383262d07c
Revises: 511231ffc1bc
Create Date: 2023-05-11 23:18:55.543689

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fb383262d07c"
down_revision = "511231ffc1bc"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("games", "published_channel_id", existing_type=sa.BIGINT(), nullable=True)


def downgrade():
    op.alter_column("games", "published_channel_id", existing_type=sa.INTEGER(), nullable=True)
