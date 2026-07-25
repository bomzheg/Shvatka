import enum
import logging
from dataclasses import dataclass
from typing import Iterable

from aiogram import Bot
from aiogram.types import Message

from shvatka.infrastructure.db.dao import PinnedMessageDao
from shvatka.tgbot.services.bot_rights import BotRights

logger = logging.getLogger(__name__)


class PinCategory(enum.StrEnum):
    level = "level"
    """Level puzzle and its hints - unpinned when the team goes to the next level."""
    bonus = "bonus"
    """Bonus hints (for a key or by a timer) - unpinned when the game is finished."""


@dataclass
class MessagePinner:
    """
    Pins messages sent to a team chat and unpins them when they get outdated.

    The bot is not necessarily an admin in a team chat (and even an admin may
    have no rights to pin), so pinning is a best-effort action: rights are
    checked first and any error is logged, but never breaks the game flow.
    """

    bot: Bot
    dao: PinnedMessageDao
    rights: BotRights

    async def pin(self, chat_id: int, messages: Iterable[Message], category: PinCategory) -> None:
        if not await self.rights.can_pin(chat_id):
            logger.info("bot can't pin messages in chat %s", chat_id)
            return
        pinned: list[int] = [
            message.message_id
            for message in messages
            if await self._pin_one(chat_id=chat_id, message_id=message.message_id)
        ]
        if not pinned:
            return
        try:
            await self.dao.save(chat_id=chat_id, category=category.value, message_ids=pinned)
        except Exception as e:
            logger.error("can't save pinned messages %s of chat %s", pinned, chat_id, exc_info=e)

    async def unpin(self, chat_id: int, category: PinCategory) -> None:
        if not await self.rights.can_pin(chat_id):
            # ids are kept, so messages can be unpinned when rights are back
            logger.info("bot can't unpin messages in chat %s", chat_id)
            return
        try:
            message_ids = await self.dao.pop_all(chat_id=chat_id, category=category.value)
        except Exception as e:
            logger.error(
                "can't get pinned messages (%s) of chat %s", category.value, chat_id, exc_info=e
            )
            return
        for message_id in message_ids:
            await self._unpin_one(chat_id=chat_id, message_id=message_id)

    async def _pin_one(self, chat_id: int, message_id: int) -> bool:
        try:
            await self.bot.pin_chat_message(
                chat_id=chat_id,
                message_id=message_id,
                disable_notification=True,
            )
        except Exception as e:
            logger.warning("can't pin message %s in chat %s", message_id, chat_id, exc_info=e)
            return False
        return True

    async def _unpin_one(self, chat_id: int, message_id: int) -> None:
        try:
            await self.bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.warning("can't unpin message %s in chat %s", message_id, chat_id, exc_info=e)
