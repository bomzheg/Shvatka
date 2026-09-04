from datetime import UTC, datetime
from unittest import mock

import pytest
from aiogram import Bot
from aiogram.types import CallbackQuery, Chat, Message, Update, User
from aiogram.types.error_event import ErrorEvent

from shvatka.common.config.models.main import DocsConfig
from shvatka.common.docs import DocsUrlFactory
from shvatka.core.utils import exceptions
from shvatka.tgbot.handlers.errors import handle_sh_error

DOCS = DocsUrlFactory(DocsConfig(base_url="https://docs.example.org", version="3.7.0"))
KEYS_URL = "https://docs.example.org/shvatka/3.7.0/player/play.html#keys"
CHAT_ID = 12345


@pytest.fixture
def bot() -> mock.AsyncMock:
    return mock.AsyncMock(spec=Bot)


def message_update() -> Update:
    return Update(update_id=1)


def callback_update(bot: Bot) -> Update:
    callback = CallbackQuery(
        id="1",
        from_user=User(id=CHAT_ID, is_bot=False, first_name="Harry"),
        chat_instance="whatever",
        data="key",
        message=Message(
            message_id=1,
            date=datetime(2024, 1, 1, tzinfo=UTC),
            chat=Chat(id=CHAT_ID, type="private"),
        ),
    )
    return Update(update_id=1, callback_query=callback.as_(bot))


def sent_texts(bot: mock.AsyncMock) -> list[str]:
    return [call.kwargs["text"] for call in bot.send_message.await_args_list]


@pytest.mark.asyncio
async def test_message_error_carries_the_doc_link(bot: mock.AsyncMock):
    error = ErrorEvent(update=message_update(), exception=exceptions.InvalidKey(chat_id=CHAT_ID))
    await handle_sh_error(error, log_chat_id=0, docs=DOCS, bot=bot)
    (text,) = sent_texts(bot)
    assert KEYS_URL in text
    assert "Ввод ключей" in text


@pytest.mark.asyncio
async def test_error_without_a_page_says_nothing_about_docs(bot: mock.AsyncMock):
    error = ErrorEvent(update=message_update(), exception=exceptions.SHError(chat_id=CHAT_ID))
    await handle_sh_error(error, log_chat_id=0, docs=DOCS, bot=bot)
    (text,) = sent_texts(bot)
    assert "Подробнее" not in text


@pytest.mark.asyncio
async def test_callback_gets_the_link_as_a_message(bot: mock.AsyncMock):
    error = ErrorEvent(update=callback_update(bot), exception=exceptions.InvalidKey())
    await handle_sh_error(error, log_chat_id=0, docs=DOCS, bot=bot)
    (text,) = sent_texts(bot)
    assert KEYS_URL in text
    assert bot.send_message.await_args.kwargs["chat_id"] == CHAT_ID


@pytest.mark.asyncio
async def test_callback_without_a_page_gets_no_extra_message(bot: mock.AsyncMock):
    error = ErrorEvent(update=callback_update(bot), exception=exceptions.SHError())
    await handle_sh_error(error, log_chat_id=0, docs=DOCS, bot=bot)
    assert [] == sent_texts(bot)
