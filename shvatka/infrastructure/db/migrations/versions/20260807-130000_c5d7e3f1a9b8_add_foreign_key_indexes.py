"""add indexes for the remaining foreign keys

Postgres does not index foreign key columns automatically. Unlike the game run
cycle indexes in the previous revision, these are not about read traffic: they
are what a DELETE on the parent row needs. Without them every such delete scans
each referencing table in full to validate the constraint, which is why deleting
or merging a player touches most of the schema.

A foreign key counts as covered only when some index has it as its first column
and is not partial. That excludes event_log.team_id, which sits second in
(game_id, team_id, at), and action_requests.team_id, whose only index is
restricted to WHERE status = 'pending'.

Revision ID: c5d7e3f1a9b8
Revises: b4c6d2e0f8a7
Create Date: 2026-08-07 13:00:00.000000

"""

from alembic import op


revision = "c5d7e3f1a9b8"
down_revision = "b4c6d2e0f8a7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix__players__promoted_by_id", "players", ["promoted_by_id"], unique=False)
    op.create_index("ix__achievements__player_id", "achievements", ["player_id"], unique=False)
    op.create_index("ix__files_info__author_id", "files_info", ["author_id"], unique=False)
    op.create_index("ix__teams__captain_id", "teams", ["captain_id"], unique=False)
    op.create_index("ix__game_files__file_id", "game_files", ["file_id"], unique=False)
    op.create_index("ix__level_files__file_id", "level_files", ["file_id"], unique=False)
    # second column of ix__event_log__game_id_team_id_at, so not usable on its own
    op.create_index("ix__event_log__team_id", "event_log", ["team_id"], unique=False)
    op.create_index("ix__notifications__actor_id", "notifications", ["actor_id"], unique=False)
    op.create_index("ix__notifications__request_id", "notifications", ["request_id"], unique=False)
    op.create_index(
        "ix__action_requests__initiator_id", "action_requests", ["initiator_id"], unique=False
    )
    # ix__action_requests_pending_team covers this column only WHERE status = 'pending'
    op.create_index("ix__action_requests__team_id", "action_requests", ["team_id"], unique=False)
    op.create_index("ix__action_requests__game_id", "action_requests", ["game_id"], unique=False)
    op.create_index(
        "ix__action_requests__responder_id", "action_requests", ["responder_id"], unique=False
    )


def downgrade():
    op.drop_index("ix__action_requests__responder_id", table_name="action_requests")
    op.drop_index("ix__action_requests__game_id", table_name="action_requests")
    op.drop_index("ix__action_requests__team_id", table_name="action_requests")
    op.drop_index("ix__action_requests__initiator_id", table_name="action_requests")
    op.drop_index("ix__notifications__request_id", table_name="notifications")
    op.drop_index("ix__notifications__actor_id", table_name="notifications")
    op.drop_index("ix__event_log__team_id", table_name="event_log")
    op.drop_index("ix__level_files__file_id", table_name="level_files")
    op.drop_index("ix__game_files__file_id", table_name="game_files")
    op.drop_index("ix__teams__captain_id", table_name="teams")
    op.drop_index("ix__files_info__author_id", table_name="files_info")
    op.drop_index("ix__achievements__player_id", table_name="achievements")
    op.drop_index("ix__players__promoted_by_id", table_name="players")
