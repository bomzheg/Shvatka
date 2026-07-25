from datetime import datetime, timedelta, timezone, tzinfo
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import GetChatMember
from aiogram.types import (
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberOwner,
    User,
)

from shvatka.tgbot.services.bot_rights import BotRights, ChatRights

CHAT_ID = 111
BOT = User(id=1, is_bot=True, first_name="bot")


class ClockMock:
    def __init__(self) -> None:
        self.now = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def __call__(self, tz: tzinfo) -> datetime:
        return self.now.astimezone(tz)


def admin(can_pin: bool) -> ChatMemberAdministrator:
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
    )


def bot_rights(member: ChatMember, clock: ClockMock) -> tuple[BotRights, AsyncMock]:
    bot = AsyncMock(Bot)
    bot.get_chat_member.return_value = member
    return BotRights(bot=bot, clock=clock), bot


@pytest.mark.parametrize(
    ("member", "can_pin"),
    [
        (ChatMemberOwner(user=BOT, is_anonymous=False), True),
        (admin(can_pin=True), True),
        (admin(can_pin=False), False),
        (ChatMemberMember(user=BOT), False),
    ],
)
def test_rights_from_member(member: ChatMember, can_pin: bool):
    assert ChatRights(can_pin_messages=can_pin) == ChatRights.from_member(member)


@pytest.mark.asyncio
async def test_rights_cached():
    clock = ClockMock()
    rights, bot = bot_rights(admin(can_pin=True), clock)

    assert await rights.can_pin(CHAT_ID)
    assert await rights.can_pin(CHAT_ID)

    assert 1 == bot.get_chat_member.await_count


@pytest.mark.asyncio
async def test_cache_expired():
    clock = ClockMock()
    rights, bot = bot_rights(admin(can_pin=True), clock)

    assert await rights.can_pin(CHAT_ID)
    clock.now += BotRights.TTL + timedelta(minutes=1)
    bot.get_chat_member.return_value = ChatMemberMember(user=BOT)

    assert not await rights.can_pin(CHAT_ID)
    assert 2 == bot.get_chat_member.await_count


@pytest.mark.asyncio
async def test_update_rights():
    clock = ClockMock()
    rights, bot = bot_rights(admin(can_pin=False), clock)
    assert not await rights.can_pin(CHAT_ID)

    rights.update(CHAT_ID, admin(can_pin=True))

    assert await rights.can_pin(CHAT_ID)
    # updated rights are cached too, no reason to ask telegram again
    assert 1 == bot.get_chat_member.await_count


@pytest.mark.asyncio
async def test_error_means_no_rights_and_isnt_cached():
    clock = ClockMock()
    rights, bot = bot_rights(admin(can_pin=True), clock)
    bot.get_chat_member.side_effect = [
        TelegramAPIError(message="chat not found", method=GetChatMember),
        admin(can_pin=True),
    ]

    assert not await rights.can_pin(CHAT_ID)
    assert await rights.can_pin(CHAT_ID)
