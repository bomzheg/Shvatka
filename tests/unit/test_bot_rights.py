from datetime import datetime, timedelta, timezone, tzinfo
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import GetChatMember
from aiogram.types import (
    Chat,
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
    ChatMemberUpdated,
    ChatPermissions,
    User,
)

from shvatka.tgbot.middlewares import BotRightsMiddleware
from shvatka.tgbot.services.bot_rights import BotRights

CHAT_ID = 111
BOT = User(id=1, is_bot=True, first_name="bot")
EVERYONE_CAN_PIN = Chat(
    id=CHAT_ID, type="supergroup", permissions=ChatPermissions(can_pin_messages=True)
)
NOBODY_CAN_PIN = Chat(
    id=CHAT_ID, type="supergroup", permissions=ChatPermissions(can_pin_messages=False)
)


class ClockMock:
    def __init__(self) -> None:
        self.now = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def __call__(self, tz: tzinfo) -> datetime:
        return self.now.astimezone(tz)


def admin(can_pin: bool, can_manage_tags: bool | None = None) -> ChatMemberAdministrator:
    return ChatMemberAdministrator(
        user=BOT,
        can_be_edited=False,
        is_anonymous=False,
        can_manage_chat=True,
        can_delete_messages=True,
        can_manage_video_chats=True,
        can_restrict_members=True,
        can_promote_members=False,
        can_change_info=True,
        can_invite_users=True,
        can_post_stories=False,
        can_edit_stories=False,
        can_delete_stories=False,
        can_pin_messages=can_pin,
        can_manage_tags=can_manage_tags,
    )


def restricted(can_pin: bool, is_member: bool = True) -> ChatMemberRestricted:
    return ChatMemberRestricted(
        user=BOT,
        is_member=is_member,
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_react_to_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=can_pin,
        can_manage_topics=False,
        can_edit_tag=False,
        until_date=0,
    )


def bot_rights(
    member: ChatMember, clock: ClockMock, chat: Chat = NOBODY_CAN_PIN
) -> tuple[BotRights, AsyncMock]:
    bot = AsyncMock(Bot)
    bot.get_chat_member.return_value = member
    bot.get_chat.return_value = chat
    return BotRights(bot=bot, clock=clock), bot


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("member", "can_pin"),
    [
        (ChatMemberOwner(user=BOT, is_anonymous=False), True),
        (admin(can_pin=True), True),
        (admin(can_pin=False), False),
        (restricted(can_pin=True), True),
        (restricted(can_pin=False), False),
        (restricted(can_pin=True, is_member=False), False),
        (ChatMemberBanned(user=BOT, until_date=0), False),
    ],
)
async def test_rights_of_member(member: ChatMember, can_pin: bool):
    rights, bot = bot_rights(member, ClockMock())

    assert can_pin == await rights.can_pin(CHAT_ID)
    # membership is enough, no reason to ask about the chat itself
    assert 0 == bot.get_chat.await_count


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("chat", "can_pin"),
    [
        (EVERYONE_CAN_PIN, True),
        (NOBODY_CAN_PIN, False),
        (Chat(id=CHAT_ID, type="supergroup"), False),
        (Chat(id=CHAT_ID, type="private"), True),
    ],
)
async def test_ordinary_member_depends_on_chat(chat: Chat, can_pin: bool):
    # pinning can be allowed to everyone in the chat, even to a plain member
    rights, bot = bot_rights(ChatMemberMember(user=BOT), ClockMock(), chat=chat)

    assert can_pin == await rights.can_pin(CHAT_ID)
    assert 1 == bot.get_chat.await_count


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("member", "can_manage_tags"),
    [
        (ChatMemberOwner(user=BOT, is_anonymous=False), True),
        (admin(can_pin=False, can_manage_tags=True), True),
        (admin(can_pin=True, can_manage_tags=False), False),
        # telegram omits the field for admins promoted before tags existed
        (admin(can_pin=True), True),
        (admin(can_pin=False), False),
        # tagging others is an admin right, no member can have it
        (ChatMemberMember(user=BOT), False),
        (restricted(can_pin=True), False),
        (ChatMemberBanned(user=BOT, until_date=0), False),
    ],
)
async def test_can_manage_tags(member: ChatMember, can_manage_tags: bool):
    rights, _ = bot_rights(member, ClockMock(), chat=EVERYONE_CAN_PIN)

    assert can_manage_tags == await rights.can_manage_tags(CHAT_ID)


@pytest.mark.asyncio
async def test_rights_cached():
    rights, bot = bot_rights(admin(can_pin=True), ClockMock())

    assert await rights.can_pin(CHAT_ID)
    assert await rights.can_pin(CHAT_ID)

    assert 1 == bot.get_chat_member.await_count


@pytest.mark.asyncio
async def test_cache_expired():
    clock = ClockMock()
    rights, bot = bot_rights(admin(can_pin=True), clock)

    assert await rights.can_pin(CHAT_ID)
    clock.now += BotRights.TTL + timedelta(minutes=1)
    bot.get_chat_member.return_value = admin(can_pin=False)

    assert not await rights.can_pin(CHAT_ID)
    assert 2 == bot.get_chat_member.await_count


@pytest.mark.asyncio
async def test_update_rights():
    rights, bot = bot_rights(admin(can_pin=False), ClockMock())
    assert not await rights.can_pin(CHAT_ID)

    rights.update(CHAT_ID, admin(can_pin=True))

    assert await rights.can_pin(CHAT_ID)
    # updated rights are cached too, no reason to ask telegram again
    assert 1 == bot.get_chat_member.await_count


@pytest.mark.asyncio
async def test_update_to_ordinary_member_forgets_rights():
    rights, bot = bot_rights(admin(can_pin=True), ClockMock(), chat=EVERYONE_CAN_PIN)
    assert await rights.can_pin(CHAT_ID)
    bot.get_chat_member.return_value = ChatMemberMember(user=BOT)

    rights.update(CHAT_ID, ChatMemberMember(user=BOT))

    # rights of a plain member depend on the chat, so they are asked again
    assert await rights.can_pin(CHAT_ID)
    assert 2 == bot.get_chat_member.await_count
    assert 1 == bot.get_chat.await_count


@pytest.mark.asyncio
async def test_middleware_updates_rights_from_update():
    rights, bot = bot_rights(admin(can_pin=False), ClockMock())
    data = {"dishka_container": SimpleNamespace(get=AsyncMock(return_value=rights))}
    handler = AsyncMock(return_value="handled")
    event = ChatMemberUpdated(
        chat=NOBODY_CAN_PIN,
        from_user=User(id=2, is_bot=False, first_name="admin"),
        date=datetime.now(tz=timezone.utc),
        old_chat_member=ChatMemberMember(user=BOT),
        new_chat_member=admin(can_pin=True),
    )

    assert "handled" == await BotRightsMiddleware()(handler, event, data)

    handler.assert_awaited_once()
    assert await rights.can_pin(CHAT_ID)
    assert 0 == bot.get_chat_member.await_count


@pytest.mark.asyncio
async def test_error_means_no_rights_and_isnt_cached():
    rights, bot = bot_rights(admin(can_pin=True), ClockMock())
    bot.get_chat_member.side_effect = [
        TelegramAPIError(message="chat not found", method=GetChatMember),
        admin(can_pin=True),
    ]

    assert not await rights.can_pin(CHAT_ID)
    assert await rights.can_pin(CHAT_ID)
