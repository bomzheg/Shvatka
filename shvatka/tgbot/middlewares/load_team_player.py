from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shvatka.core.services.player import get_full_team_player, get_my_team
from shvatka.core.utils.exceptions import PlayerNotInTeam
from shvatka.tgbot.utils.data import SHMiddlewareData


class TeamPlayerMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: SHMiddlewareData,
    ) -> Any:
        if (player := data.get("player", None)) is not None and "team_player" not in data:
            if "team" not in data or data["team"] is None:
                team = await get_my_team(player=player, dao=data["dao"].team_player)
                data["team"] = team
            else:
                team = data["team"]
            try:
                team_player = await get_full_team_player(player, team, data["dao"].team_player)
            except PlayerNotInTeam:
                team_player = None
            data["team_player"] = team_player
        else:
            data["team_player"] = None
        result = await handler(event, data)  # type: ignore[arg-type]
        return result
