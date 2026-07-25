import logging
import typing
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo

from aiogram import Bot
from aiogram.types import ChatMember, ChatMemberAdministrator, ChatMemberOwner

from shvatka.core.utils.datetime_utils import tz_utc

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatRights:
    """What the bot is allowed to do in a chat."""

    can_pin_messages: bool

    @classmethod
    def from_member(cls, member: ChatMember) -> "ChatRights":
        match member:
            case ChatMemberOwner():
                return cls(can_pin_messages=True)
            case ChatMemberAdministrator():
                return cls(can_pin_messages=bool(member.can_pin_messages))
            case _:
                return cls(can_pin_messages=False)


NO_RIGHTS = ChatRights(can_pin_messages=False)


@dataclass(frozen=True)
class _CachedRights:
    rights: ChatRights
    actual_until: datetime

    def is_actual(self, now: datetime) -> bool:
        return now < self.actual_until


class BotRights:
    """
    Rights of the bot in chats, cached in memory.

    The bot may or may not be an admin in a team chat, and asking telegram
    about it before every action is too expensive. So rights are kept for
    TTL and refreshed either on expiration or when telegram itself reports
    a change of the bot's membership (see the my_chat_member handler).
    """

    TTL = timedelta(minutes=30)

    def __init__(
        self, bot: Bot, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        self.bot = bot
        self.clock = clock
        self.cache: dict[int, _CachedRights] = {}

    async def can_pin(self, chat_id: int) -> bool:
        return (await self.get(chat_id)).can_pin_messages

    async def get(self, chat_id: int) -> ChatRights:
        cached = self.cache.get(chat_id)
        if cached is not None and cached.is_actual(self.clock(tz_utc)):
            return cached.rights
        try:
            member = await self.bot.get_chat_member(chat_id=chat_id, user_id=self.bot.id)
        except Exception as e:
            # not cached: it can be a temporary error, next time we'll ask again
            logger.warning("can't get bot rights in chat %s", chat_id, exc_info=e)
            return NO_RIGHTS
        return self.save(chat_id, ChatRights.from_member(member))

    def update(self, chat_id: int, member: ChatMember) -> None:
        """Telegram reported the new membership of the bot, no need to ask it again."""
        self.save(chat_id, ChatRights.from_member(member))

    def save(self, chat_id: int, rights: ChatRights) -> ChatRights:
        self.cache[chat_id] = _CachedRights(
            rights=rights,
            actual_until=self.clock(tz_utc) + self.TTL,
        )
        return rights
