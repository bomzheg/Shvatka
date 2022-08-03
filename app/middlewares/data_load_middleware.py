from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.dao.holder import HolderDao
from app.models import dto
from app.services.chat import upsert_chat
from app.services.player import upsert_player
from app.services.team import get_by_chat
from app.services.user import upsert_user


class LoadDataMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any]
    ) -> Any:
        holder_dao = data["dao"]
        user = await save_user(data, holder_dao)
        data["user"] = user
        data["player"] = await save_player(user, holder_dao)
        chat = await save_chat(data, holder_dao)
        data["chat"] = chat
        data["team"] = await load_team(chat, holder_dao)
        data["game"] = None
        result = await handler(event, data)
        return result


async def save_user(data: dict[str, Any], holder_dao: HolderDao) -> dto.User:
    return await upsert_user(
        dto.User.from_aiogram(data["event_from_user"]),
        holder_dao.user
    )


async def save_player(user: dto.User, holder_dao: HolderDao) -> dto.Player:
    return await upsert_player(user, holder_dao.player)


async def save_chat(data: dict[str, Any], holder_dao: HolderDao) -> dto.Chat:
    return await upsert_chat(
        dto.Chat.from_aiogram(data["event_chat"]),
        holder_dao.chat
    )


async def load_team(chat: dto.Chat, holder_dao: HolderDao) -> dto.Team:
    return await get_by_chat(chat, holder_dao.team)
