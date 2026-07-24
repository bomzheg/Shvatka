import enum
import logging
from dataclasses import dataclass
from typing import Iterable

from aiogram import Bot
from aiogram.types import Message

from shvatka.infrastructure.db.dao import PinnedMessageDao

logger = logging.getLogger(__name__)


class PinCategory(enum.StrEnum):
    level = "level"
    """Загадка уровня и подсказки к нему - открепляются при переходе на следующий уровень."""
    bonus = "bonus"
    """Бонусные подсказки (за ключ или по таймеру) - открепляются в конце игры."""


@dataclass
class MessagePinner:
    """
    Закрепляет отправленные командам сообщения и открепляет их, когда они устарели.

    Бот может не быть админом в чате команды (или не иметь права закреплять),
    поэтому любая ошибка при (от)креплении - ожидаемая ситуация,
    она логируется и не ломает остальной сценарий игры.
    """

    bot: Bot
    dao: PinnedMessageDao

    async def pin(self, chat_id: int, messages: Iterable[Message], category: PinCategory) -> None:
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
