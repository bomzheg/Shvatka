"""add file_info table

Revision ID: 50b4aa6c0252
Revises: 555d635df99f
Create Date: 2022-11-03 23:26:18.870227

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "50b4aa6c0252"
down_revision = "555d635df99f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "files_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("guid", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.Text(), nullable=True),
        sa.Column("extension", sa.Text(), nullable=True),
        sa.Column("file_id", sa.Text(), nullable=True),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["players.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guid"),
    )


def downgrade():
    op.drop_table("files_info")
