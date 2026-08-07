"""add query and foreign key indexes

Postgres does not index foreign key columns automatically, and this schema had
almost no non-unique indexes: every per-game/per-team/per-player lookup fell back
to a sequential scan, and every parent DELETE scanned each child table in full.

Revision ID: b4c6d2e0f8a7
Revises: a3b5c1d9e7f6
Create Date: 2026-08-07 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b4c6d2e0f8a7"
down_revision = "a3b5c1d9e7f6"
branch_labels = None
depends_on = None

# (name, table, columns, kwargs) — created in order, dropped in reverse
INDEXES: list[tuple[str, str, list, dict]] = [
    # --- log_keys: the largest and fastest growing table ---
    # all per-level key queries filter game_id + level_time_id + team_id, but
    # level_time_id alone already narrows to a single team's single level
    ("ix__log_keys__level_time_id", "log_keys", ["level_time_id"], {}),
    ("ix__log_keys__game_id_enter_time", "log_keys", ["game_id", "enter_time"], {}),
    ("ix__log_keys__player_id", "log_keys", ["player_id"], {}),
    ("ix__log_keys__team_id", "log_keys", ["team_id"], {}),
    ("ix__log_keys__event_id", "log_keys", ["event_id"], {}),
    # --- levels_times ---
    # serves both the current-level lookup (game + team, latest start_at) and the
    # whole-game listing ordered by team_id, start_at
    (
        "ix__levels_times__game_id_team_id_start_at",
        "levels_times",
        ["game_id", "team_id", "start_at"],
        {},
    ),
    ("ix__levels_times__team_id", "levels_times", ["team_id"], {}),
    # --- levels: unique constraint leads with author_id, so game_id was unindexed ---
    ("ix__levels__game_id_number_in_game", "levels", ["game_id", "number_in_game"], {}),
    # --- team_players: resolves "which team is this player on" on nearly every request ---
    ("ix__team_players__player_id", "team_players", ["player_id"], {}),
    ("ix__team_players__team_id", "team_players", ["team_id"], {}),
    # --- waivers: unique constraint leads with game_id ---
    ("ix__waivers__player_id", "waivers", ["player_id"], {}),
    ("ix__waivers__team_id", "waivers", ["team_id"], {}),
    # --- event_log ---
    ("ix__event_log__game_id_team_id_at", "event_log", ["game_id", "team_id", "at"], {}),
    ("ix__event_log__level_time_id", "event_log", ["level_time_id"], {}),
    # --- remaining unindexed foreign keys ---
    ("ix__organizers__game_id", "organizers", ["game_id"], {}),
    ("ix__achievements__player_id", "achievements", ["player_id"], {}),
    ("ix__files_info__author_id", "files_info", ["author_id"], {}),
    ("ix__level_files__file_id", "level_files", ["file_id"], {}),
    ("ix__game_files__file_id", "game_files", ["file_id"], {}),
    ("ix__timers_log__level_time_id", "timers_log", ["level_time_id"], {}),
    ("ix__timers_log__event_id", "timers_log", ["event_id"], {}),
    ("ix__teams__captain_id", "teams", ["captain_id"], {}),
    ("ix__players__promoted_by_id", "players", ["promoted_by_id"], {}),
    ("ix__notifications__actor_id", "notifications", ["actor_id"], {}),
    ("ix__notifications__request_id", "notifications", ["request_id"], {}),
    ("ix__action_requests__initiator_id", "action_requests", ["initiator_id"], {}),
    ("ix__action_requests__game_id", "action_requests", ["game_id"], {}),
    ("ix__action_requests__responder_id", "action_requests", ["responder_id"], {}),
]


def upgrade():
    for name, table, columns, kwargs in INDEXES:
        op.create_index(name, table, columns, unique=False, **kwargs)
    # the planner needs fresh stats to start choosing the new indexes
    op.execute(sa.text("ANALYZE log_keys"))
    op.execute(sa.text("ANALYZE levels_times"))
    op.execute(sa.text("ANALYZE levels"))
    op.execute(sa.text("ANALYZE team_players"))
    op.execute(sa.text("ANALYZE waivers"))


def downgrade():
    for name, table, _columns, _kwargs in reversed(INDEXES):
        op.drop_index(name, table_name=table)
