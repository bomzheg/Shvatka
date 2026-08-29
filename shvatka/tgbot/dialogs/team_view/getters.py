from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.players.player import get_team_players
from shvatka.core.services.team import get_played_games, get_team_by_id, get_teams
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.dialogs.outdated import get_actual_team_player

from .common import get_active_filter, get_archive_filter


@inject
async def teams_getter(
    dao: FromDishka[HolderDao], dialog_manager: DialogManager, **_
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


@inject
async def team_getter(dao: FromDishka[HolderDao], dialog_manager: DialogManager, **_):
    team_id: int = dialog_manager.dialog_data["team_id"]
    return await team_card(await get_team_by_id(team_id, dao.team), dao)


@inject
async def my_team_getter(dao: FromDishka[HolderDao], identity: FromDishka[IdentityProvider], **_):
    """The card of the team the player is in *at this moment*.

    Deliberately resolved on every render instead of remembering a team id when
    the dialog started: between the two the player may have been removed from
    the team, and then there is no card to show at all.
    """
    return await team_card((await get_actual_team_player(identity)).team, dao)


async def team_card(team: dto.Team, dao: HolderDao) -> dict[str, Any]:
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
