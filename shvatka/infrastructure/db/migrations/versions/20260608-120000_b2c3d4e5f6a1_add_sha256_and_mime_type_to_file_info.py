"""add sha256 and mime_type to file_info

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-06-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a1"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("files_info", sa.Column("sha256", sa.Text(), nullable=True))
    op.add_column("files_info", sa.Column("mime_type", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix__files_info__sha256"),
        "files_info",
        ["sha256"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix__files_info__sha256"), table_name="files_info")
    op.drop_column("files_info", "mime_type")
    op.drop_column("files_info", "sha256")
