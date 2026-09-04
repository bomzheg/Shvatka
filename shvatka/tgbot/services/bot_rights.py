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
    can_pin_messages: bool
    can_manage_tags: bool


NO_RIGHTS = ChatRights(can_pin_messages=False, can_manage_tags=False)


def rights_of_member(member: ChatMember) -> ChatRights | None:
    match member:
        case ChatMemberOwner():
            return ChatRights(can_pin_messages=True, can_manage_tags=True)
        case ChatMemberAdministrator():
            return ChatRights(
                can_pin_messages=bool(member.can_pin_messages),
                # telegram omits can_manage_tags for admins promoted before the
                # right existed, it defaults to can_pin_messages then
                can_manage_tags=bool(
                    member.can_pin_messages
                    if member.can_manage_tags is None
                    else member.can_manage_tags
                ),
            )
        case ChatMemberRestricted():
            # restricted member can be forbidden to pin even if everyone else can
            return ChatRights(
                can_pin_messages=member.is_member and member.can_pin_messages,
                # tagging others is an admin right, no member has it
                can_manage_tags=False,
            )
        case ChatMemberMember():
            return None
        case _:  # left the chat or banned in it
            return NO_RIGHTS


def rights_of_chat(chat: Chat) -> ChatRights:
    if chat.type == ChatType.PRIVATE:
        return ChatRights(can_pin_messages=True, can_manage_tags=False)
    permissions = chat.permissions
    return ChatRights(
        can_pin_messages=bool(permissions and permissions.can_pin_messages),
        # tagging others is an admin right, it can't be granted to everyone
        can_manage_tags=False,
    )


@dataclass(frozen=True)
class _CachedRights:
    rights: ChatRights
    actual_until: datetime

    def is_actual(self, now: datetime) -> bool:
        return now < self.actual_until


class BotRights:
    TTL = timedelta(minutes=30)

    def __init__(
        self, bot: Bot, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        self.bot = bot
        self.clock = clock
        self.cache: dict[int, _CachedRights] = {}

    async def can_pin(self, chat_id: int) -> bool:
        return (await self.get(chat_id)).can_pin_messages

    async def can_manage_tags(self, chat_id: int) -> bool:
        return (await self.get(chat_id)).can_manage_tags

    async def get(self, chat_id: int) -> ChatRights:
        cached = self.cache.get(chat_id)
        if cached is not None and cached.is_actual(self.clock(tz_utc)):
            return cached.rights
        try:
            rights = await self._load(chat_id)
        except Exception as e:  # noqa: BLE001
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
