"""add indexes for the game run cycle

Postgres does not index foreign key columns automatically, and this schema had
almost no non-unique indexes, so the tables read while a game runs were scanned
in full on every lookup. In production these four alone account for 95.6% of all
sequential tuple reads, log_keys for 80.1% of them with no index scan ever
recorded against it.

Tables outside the game run cycle are deliberately left alone: together they are
under 0.5% of sequential reads and already serve most lookups from an index.

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
    # --- organizers and timers, also read while a game runs ---
    ("ix__organizers__game_id", "organizers", ["game_id"], {}),
    ("ix__timers_log__level_time_id", "timers_log", ["level_time_id"], {}),
    ("ix__timers_log__event_id", "timers_log", ["event_id"], {}),
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
