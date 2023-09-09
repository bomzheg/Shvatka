from aiogram_dialog import DialogManager

from shvatka.core.models import dto
from shvatka.core.services.player import get_team_players
from shvatka.core.services.team import get_teams, get_team_by_id, get_played_games
from shvatka.infrastructure.db.dao.holder import HolderDao
from .common import get_active_filter, get_archive_filter


async def teams_getter(
    dao: HolderDao, dialog_manager: DialogManager, **_
) -> dict[str, list[dto.Team]]:
    return {
        "teams": await get_teams(
            dao.team,
            active=get_active_filter(dialog_manager),
            archive=get_archive_filter(dialog_manager),
        ),
        "active": get_active_filter(dialog_manager),
        "archive": get_archive_filter(dialog_manager),
    }


async def team_getter(dao: HolderDao, dialog_manager: DialogManager, **_):
    team_id: int = dialog_manager.dialog_data["team_id"]
    team = await get_team_by_id(team_id, dao.team)
    players = await get_team_players(team=team, dao=dao.team_player)
    games = await get_played_games(team=team, dao=dao.team)
    games_numbers = [str(game.number) for game in games]
    return {
        "team": team,
        "players": players,
        "games": games,
        "game_numbers": games_numbers,
    }


async def filter_getter(dialog_manager: DialogManager, **_):
    return {
        "active": get_active_filter(dialog_manager),
        "archive": get_archive_filter(dialog_manager),
    }
