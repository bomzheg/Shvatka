from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.infrastructure.db.dao.holder import HolderDao
from src.core.models import dto
from src.core.services.player import get_full_team_player, get_my_team
from src.core.utils.exceptions import PlayerNotInTeam


class TeamPlayerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        dao: HolderDao = data["dao"]
        player: dto.Player = data["player"]
        team = await get_my_team(player=player, dao=dao.team_player)
        try:
            team_player = await get_full_team_player(player, team, dao.team_player)
        except PlayerNotInTeam:
            team_player = None
        data["team_player"] = team_player
        result = await handler(event, data)
        return result
