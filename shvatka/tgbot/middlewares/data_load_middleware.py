from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject

from shvatka.core.models import dto
from shvatka.core.services.chat import upsert_chat
from shvatka.core.services.game import get_active
from shvatka.core.services.player import upsert_player
from shvatka.core.services.team import get_by_chat
from shvatka.core.services.user import upsert_user
from shvatka.infrastructure.db.dao.holder import HolderDao


class LoadDataMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        holder_dao: HolderDao = data["dao"]
        user = await save_user(data, holder_dao)
        data["user"] = user
        data["player"] = await save_player(user, holder_dao)
        chat = await save_chat(data, holder_dao)
        data["chat"] = chat
        data["team"] = await load_team(chat, holder_dao)
        data["game"] = await get_active(holder_dao.game)
        result = await handler(event, data)
        return result


async def save_user(data: dict[str, Any], holder_dao: HolderDao) -> dto.User | None:
    user: types.User = data.get("event_from_user", None)
    if not user:
        return None
    return await upsert_user(dto.User.from_aiogram(user), holder_dao.user)


async def save_player(user: dto.User | None, holder_dao: HolderDao) -> dto.Player | None:
    if not user:
        return None
    return await upsert_player(user, holder_dao.player)


async def save_chat(data: dict[str, Any], holder_dao: HolderDao) -> dto.Chat | None:
    chat: dto.Chat = data.get("event_chat", None)
    if not chat:
        return None
    return await upsert_chat(dto.Chat.from_aiogram(chat), holder_dao.chat)


async def load_team(chat: dto.Chat | None, holder_dao: HolderDao) -> dto.Team | None:
    if not chat:
        return None
    return await get_by_chat(chat, holder_dao.team)
