import pytest
from aiogram import Dispatcher
from aiogram_dialog.test_tools import BotClient, MockMessageManager
from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator

from shvatka.models import enums, dto
from tests.fixtures.chat_constants import create_tg_chat
from tests.fixtures.user_constants import create_tg_from_dto
from tgbot.views.commands import NEW_GAME_COMMAND


@pytest.fixture
def author_client(author: dto.Player, dp: Dispatcher):
    client = BotClient(dp)
    client.user = create_tg_from_dto(author.user)
    client.chat = create_tg_chat(
        type_=enums.ChatType.private,
        first_name=client.user.first_name,
        last_name=client.user.last_name,
    )
    return client


@pytest.mark.asyncio
async def test_create_game(author_client: BotClient, message_manager: MockMessageManager):
    await author_client.send("/" + NEW_GAME_COMMAND.command)
    first_message = message_manager.one_message()
    assert "Выбираем название игры" in first_message.text
    assert first_message.reply_markup

    message_manager.reset_history()
    await author_client.send("test_game")
    first_message = message_manager.sent_messages[1]
    assert "test_game" in first_message.text
    assert "Выбери уровни которые нужно добавить" in first_message.text
    assert first_message.reply_markup

    callback_id = await author_client.click(
        first_message,
        InlineButtonTextLocator("⤴Не создавать игру"),
    )
    message_manager.assert_answered(callback_id)
