"""add game number

Revision ID: 852f6bcc741f
Revises: 061da47bee48
Create Date: 2023-01-28 15:21:11.148546

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "852f6bcc741f"
down_revision = "51e122b5e734"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("games", sa.Column("number", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("games", "number")
