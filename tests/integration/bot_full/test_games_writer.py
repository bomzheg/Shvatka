import pytest
from aiogram.enums import ContentType
from aiogram_dialog.test_tools import BotClient, MockMessageManager
from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator

from shvatka.tgbot.views.commands import NEW_GAME_COMMAND


@pytest.mark.asyncio
async def test_exit_write_game(author_client: BotClient, message_manager: MockMessageManager):
    await author_client.send("/" + NEW_GAME_COMMAND.command)
    first_message = message_manager.one_message()
    assert first_message.text is not None
    assert "Выбираем название игры" in first_message.text
    assert first_message.reply_markup

    message_manager.reset_history()
    await author_client.send("test_game")
    new_message = message_manager.one_message()
    assert new_message.text is not None
    assert "test_game" in new_message.text
    assert "Выбери уровни которые нужно добавить" in new_message.text
    assert new_message.reply_markup

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator("🔙Не создавать игру"),
    )
    message_manager.assert_answered(callback_id)
    msg = message_manager.one_message()
    assert msg.content_type == ContentType.UNKNOWN
