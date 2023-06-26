from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shvatka.core.services.player import get_full_team_player, get_my_team
from shvatka.core.utils.exceptions import PlayerNotInTeam
from shvatka.tgbot.utils.data import MiddlewareData


class TeamPlayerMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        team = await get_my_team(player=(data["player"]), dao=data["dao"].team_player)
        if team:
            data["team"] = data.get("team", team) or team  # if team already setted as None
        try:
            team_player = await get_full_team_player(data["player"], team, data["dao"].team_player)
        except PlayerNotInTeam:
            team_player = None
        data["team_player"] = team_player
        result = await handler(event, data)
        return result
