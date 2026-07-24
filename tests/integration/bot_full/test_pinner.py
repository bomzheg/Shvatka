import typing
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import PinChatMessage
from aiogram.types import Chat, Message
from dishka import AsyncContainer

from shvatka.infrastructure.db.dao import PinnedMessageDao
from shvatka.tgbot.views.pinner import MessagePinner, PinCategory
from tests.fixtures.file_storage import CHAT_ID


@pytest_asyncio.fixture
async def pinner(dishka_request: AsyncContainer):
    pinner_ = await dishka_request.get(MessagePinner)
    for category in PinCategory:
        await pinner_.dao.pop_all(chat_id=CHAT_ID, category=category.value)
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
async def test_pin_error_dont_break_flow(
    pinner: MessagePinner, bot_session: BaseSession, dishka_request: AsyncContainer
):
    # бот может не быть админом чата - тогда телеграм ответит ошибкой
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

    # ошибка на первом сообщении не мешает открепить остальные
    assert [1, 2] == [request.message_id for request in requests(bot_session, "unpinChatMessage")]
