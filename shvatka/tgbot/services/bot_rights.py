import logging
import typing
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo

from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.types import (
    Chat,
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
)

from shvatka.core.utils.datetime_utils import tz_utc

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatRights:
    """What the bot is allowed to do in a chat."""

    can_pin_messages: bool


NO_RIGHTS = ChatRights(can_pin_messages=False)


def rights_of_member(member: ChatMember) -> ChatRights | None:
    """
    Rights granted by the membership itself.

    None means the membership grants nothing on its own: an ordinary member
    can do only what is allowed to everyone, so the default permissions of
    the chat have to be checked (see ``rights_of_chat``).
    """
    match member:
        case ChatMemberOwner():
            return ChatRights(can_pin_messages=True)
        case ChatMemberAdministrator():
            return ChatRights(can_pin_messages=bool(member.can_pin_messages))
        case ChatMemberRestricted():
            # restricted member can be forbidden to pin even if everyone else can
            return ChatRights(can_pin_messages=member.is_member and member.can_pin_messages)
        case ChatMemberMember():
            return None
        case _:  # left the chat or banned in it
            return NO_RIGHTS


def rights_of_chat(chat: Chat) -> ChatRights:
    """What is allowed to everyone in the chat."""
    if chat.type == ChatType.PRIVATE:
        return ChatRights(can_pin_messages=True)
    permissions = chat.permissions
    return ChatRights(can_pin_messages=bool(permissions and permissions.can_pin_messages))


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
    a change of the bot's membership (see BotRightsMiddleware).
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
            rights = await self._load(chat_id)
        except Exception as e:
            # not cached: it can be a temporary error, next time we'll ask again
            logger.warning("can't get bot rights in chat %s", chat_id, exc_info=e)
            return NO_RIGHTS
        return self.save(chat_id, rights)

    async def _load(self, chat_id: int) -> ChatRights:
        member = await self.bot.get_chat_member(chat_id=chat_id, user_id=self.bot.id)
        if (rights := rights_of_member(member)) is not None:
            return rights
        return rights_of_chat(await self.bot.get_chat(chat_id))

    def update(self, chat_id: int, member: ChatMember) -> None:
        """Telegram reported the new membership of the bot, no need to ask it again."""
        rights = rights_of_member(member)
        if rights is None:
            # ordinary member, rights depend on the chat - ask telegram when needed
            self.forget(chat_id)
        else:
            self.save(chat_id, rights)

    def save(self, chat_id: int, rights: ChatRights) -> ChatRights:
        self.cache[chat_id] = _CachedRights(
            rights=rights,
            actual_until=self.clock(tz_utc) + self.TTL,
        )
        return rights

    def forget(self, chat_id: int) -> None:
        self.cache.pop(chat_id, None)
