"""add level_files and game_files m2m tables

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-06-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a1b2c3"
down_revision = "c3d4e5f6a1b2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "level_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("level_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["level_id"],
            ["levels.id"],
            name=op.f("level_files_level_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["files_info.id"],
            name=op.f("level_files_file_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__level_files")),
        sa.UniqueConstraint("level_id", "file_id", name=op.f("uq__level_files__level_id")),
    )
    op.create_table(
        "game_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name=op.f("game_files_game_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["files_info.id"],
            name=op.f("game_files_file_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__game_files")),
        sa.UniqueConstraint("game_id", "file_id", name=op.f("uq__game_files__game_id")),
    )

    # Fill both tables from the existing level scenarios. File references are stored
    # in the scenario json under "file_guid" (and an optional "thumb_guid") keys at
    # arbitrary depth, so collect every such guid recursively and join it to the
    # actual files by guid.
    op.execute(
        """
        WITH level_guids AS (
            SELECT l.id AS level_id, l.game_id AS game_id, (g.value #>> '{}') AS guid
            FROM levels l,
                 LATERAL jsonb_path_query(l.scenario::jsonb, 'lax $.**.file_guid') AS g(value)
            UNION
            SELECT l.id, l.game_id, (g.value #>> '{}')
            FROM levels l,
                 LATERAL jsonb_path_query(l.scenario::jsonb, 'lax $.**.thumb_guid') AS g(value)
        )
        INSERT INTO level_files (level_id, file_id)
        SELECT DISTINCT lg.level_id, fi.id
        FROM level_guids lg
        JOIN files_info fi ON fi.guid = lg.guid
        WHERE lg.guid IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )
    op.execute(
        """
        WITH level_guids AS (
            SELECT l.id AS level_id, l.game_id AS game_id, (g.value #>> '{}') AS guid
            FROM levels l,
                 LATERAL jsonb_path_query(l.scenario::jsonb, 'lax $.**.file_guid') AS g(value)
            UNION
            SELECT l.id, l.game_id, (g.value #>> '{}')
            FROM levels l,
                 LATERAL jsonb_path_query(l.scenario::jsonb, 'lax $.**.thumb_guid') AS g(value)
        )
        INSERT INTO game_files (game_id, file_id)
        SELECT DISTINCT lg.game_id, fi.id
        FROM level_guids lg
        JOIN files_info fi ON fi.guid = lg.guid
        WHERE lg.guid IS NOT NULL AND lg.game_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )


def downgrade():
    op.drop_table("game_files")
    op.drop_table("level_files")
