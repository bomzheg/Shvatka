import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import ChatMemberUpdated

from shvatka.tgbot.services.bot_rights import BotRights
from shvatka.tgbot.utils.data import SHMiddlewareData

logger = logging.getLogger(__name__)


class BotRightsMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore[override]
        self,
        handler: Callable[[ChatMemberUpdated, dict[str, Any]], Awaitable[Any]],
        event: ChatMemberUpdated,
        data: SHMiddlewareData,
    ) -> Any:
        logger.info(
            "bot membership in chat %s changed to %s",
            event.chat.id,
            event.new_chat_member.status,
        )
        bot_rights = await data["dishka_container"].get(BotRights)
        bot_rights.update(event.chat.id, event.new_chat_member)
        return await handler(event, data)  # type: ignore[arg-type]
