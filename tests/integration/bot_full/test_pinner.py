import typing
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import PinChatMessage
from aiogram.types import Chat, ChatMemberMember, ChatMemberOwner, Message, User
from dishka import AsyncContainer

from shvatka.infrastructure.db.dao import PinnedMessageDao
from shvatka.tgbot.views.pinner import MessagePinner, PinCategory
from tests.fixtures.file_storage import CHAT_ID

BOT_USER = User(id=1, is_bot=True, first_name="bot")


@pytest_asyncio.fixture
async def pinner(dishka_request: AsyncContainer):
    pinner_ = await dishka_request.get(MessagePinner)
    for category in PinCategory:
        await pinner_.dao.pop_all(chat_id=CHAT_ID, category=category.value)
    # bot is an admin who can pin, so it doesn't ask telegram about its rights
    pinner_.rights.update(CHAT_ID, ChatMemberOwner(user=BOT_USER, is_anonymous=False))
    return pinner_


def message(message_id: int) -> Message:
    return Message(
        message_id=message_id,
        date=datetime.now(tz=timezone.utc),
        chat=Chat(id=CHAT_ID, type="supergroup"),
    )


def requests(bot_session: BaseSession, api_method: str) -> list:
    session = typing.cast(MagicMock, bot_session)
    return [
        call.args[1]
        for call in session.mock_calls
        if getattr(call.args[1], "__api_method__", None) == api_method
    ]


@pytest.mark.asyncio
async def test_pin_all_parts_and_unpin(pinner: MessagePinner, bot_session: BaseSession):
    await pinner.pin(CHAT_ID, [message(1), message(2), message(3)], PinCategory.level)

    pins = requests(bot_session, "pinChatMessage")
    assert [1, 2, 3] == [request.message_id for request in pins]
    assert all(request.chat_id == CHAT_ID for request in pins)
    assert all(request.disable_notification for request in pins)

    await pinner.unpin(CHAT_ID, PinCategory.level)

    unpins = requests(bot_session, "unpinChatMessage")
    assert [1, 2, 3] == [request.message_id for request in unpins]


@pytest.mark.asyncio
async def test_unpin_forgets_messages(pinner: MessagePinner, bot_session: BaseSession):
    await pinner.pin(CHAT_ID, [message(1)], PinCategory.level)
    await pinner.unpin(CHAT_ID, PinCategory.level)
    await pinner.unpin(CHAT_ID, PinCategory.level)

    assert 1 == len(requests(bot_session, "unpinChatMessage"))


@pytest.mark.asyncio
async def test_categories_are_independent(pinner: MessagePinner, bot_session: BaseSession):
    await pinner.pin(CHAT_ID, [message(1)], PinCategory.level)
    await pinner.pin(CHAT_ID, [message(2)], PinCategory.bonus)

    await pinner.unpin(CHAT_ID, PinCategory.level)
    assert [1] == [request.message_id for request in requests(bot_session, "unpinChatMessage")]

    await pinner.unpin(CHAT_ID, PinCategory.bonus)
    assert [1, 2] == [request.message_id for request in requests(bot_session, "unpinChatMessage")]


@pytest.mark.asyncio
async def test_dont_pin_without_rights(
    pinner: MessagePinner, bot_session: BaseSession, dishka_request: AsyncContainer
):
    pinner.rights.update(CHAT_ID, ChatMemberMember(user=BOT_USER))

    await pinner.pin(CHAT_ID, [message(1)], PinCategory.level)

    assert [] == requests(bot_session, "pinChatMessage")
    dao = await dishka_request.get(PinnedMessageDao)
    assert [] == await dao.pop_all(chat_id=CHAT_ID, category=PinCategory.level.value)


@pytest.mark.asyncio
async def test_pinned_messages_kept_until_rights_are_back(
    pinner: MessagePinner, bot_session: BaseSession
):
    await pinner.pin(CHAT_ID, [message(1)], PinCategory.level)
    pinner.rights.update(CHAT_ID, ChatMemberMember(user=BOT_USER))

    await pinner.unpin(CHAT_ID, PinCategory.level)
    assert [] == requests(bot_session, "unpinChatMessage")

    pinner.rights.update(CHAT_ID, ChatMemberOwner(user=BOT_USER, is_anonymous=False))
    await pinner.unpin(CHAT_ID, PinCategory.level)
    assert [1] == [request.message_id for request in requests(bot_session, "unpinChatMessage")]


@pytest.mark.asyncio
async def test_pin_error_dont_break_flow(
    pinner: MessagePinner, bot_session: BaseSession, dishka_request: AsyncContainer
):
    # even an admin bot can get an error from telegram
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [TelegramAPIError(message="not enough rights", method=PinChatMessage)]

    await pinner.pin(CHAT_ID, [message(1)], PinCategory.level)

    dao = await dishka_request.get(PinnedMessageDao)
    assert [] == await dao.pop_all(chat_id=CHAT_ID, category=PinCategory.level.value)


@pytest.mark.asyncio
async def test_unpin_error_dont_break_flow(pinner: MessagePinner, bot_session: BaseSession):
    await pinner.pin(CHAT_ID, [message(1), message(2)], PinCategory.level)
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [
        TelegramAPIError(message="not enough rights", method=PinChatMessage),
        {},
    ]

    await pinner.unpin(CHAT_ID, PinCategory.level)

    # an error on the first message doesn't prevent unpinning the rest
    assert [1, 2] == [request.message_id for request in requests(bot_session, "unpinChatMessage")]
