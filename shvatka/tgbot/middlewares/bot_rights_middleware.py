import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import ChatMemberUpdated

from shvatka.tgbot.services.bot_rights import BotRights
from shvatka.tgbot.utils.data import SHMiddlewareData

logger = logging.getLogger(__name__)


class BotRightsMiddleware(BaseMiddleware):
    """
    Keeps cached rights of the bot up to date.

    Telegram reports every change of the bot's membership, so the cache can
    be refreshed for free. It's a middleware and not a handler to not consume
    my_chat_member updates other handlers may be interested in.
    """

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
