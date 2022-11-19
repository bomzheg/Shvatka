from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import get_team_player, get_my_team


class TeamPlayerMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        dao: HolderDao = data["dao"]
        player: dto.Player = data["player"]
        team = await get_my_team(player=player, dao=dao.player_in_team)
        team_player = await get_team_player(player, team, dao.player_in_team)
        data["team_player"] = team_player
        result = await handler(event, data)
        return result
