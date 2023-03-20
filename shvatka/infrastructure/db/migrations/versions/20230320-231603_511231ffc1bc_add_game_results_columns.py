"""add game results columns

Revision ID: 511231ffc1bc
Revises: c076368bb3aa
Create Date: 2023-03-20 23:16:03.669959

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "511231ffc1bc"
down_revision = "c076368bb3aa"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("games", sa.Column("results_picture_file_id", sa.String(), nullable=True))
    op.add_column("games", sa.Column("keys_url", sa.String(), nullable=True))


def downgrade():
    op.drop_column("games", "keys_url")
    op.drop_column("games", "results_picture_file_id")
