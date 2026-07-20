from aiogram.filters.callback_data import CallbackData

# New merge requests use the generic action-request keyboard; these callback data
# classes remain so the buttons on messages posted before that change keep working.


class TeamMergeCD(CallbackData, prefix="team_merge"):
    primary_team_id: int
    secondary_team_id: int


class PlayerMergeCD(CallbackData, prefix="player_merge"):
    primary_player_id: int
    secondary_player_id: int
