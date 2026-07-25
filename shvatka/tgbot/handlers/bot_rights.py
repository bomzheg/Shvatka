import logging

from aiogram import Router
from aiogram.types import ChatMemberUpdated
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.tgbot.services.bot_rights import BotRights

logger = logging.getLogger(__name__)


@inject
async def bot_rights_changed(
    event: ChatMemberUpdated,
    bot_rights: FromDishka[BotRights],
) -> None:
    logger.info(
        "bot membership in chat %s changed to %s",
        event.chat.id,
        event.new_chat_member.status,
    )
    bot_rights.update(event.chat.id, event.new_chat_member)


def setup() -> Router:
    router = Router(name=__name__)
    router.my_chat_member.register(bot_rights_changed)
    return router
