import pytest
from aiogram_dialog.test_tools import BotClient, MockMessageManager
from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator
from aiogram_tests.mocked_bot import MockedBot

from infrastructure.db.dao.holder import HolderDao
from shvatka.models import dto
from tgbot.views.commands import NEW_LEVEL_COMMAND


@pytest.mark.asyncio
async def test_exit_write_game(
    author: dto.Player,
    author_client: BotClient,
    message_manager: MockMessageManager,
    dao: HolderDao,
    bot: MockedBot,
):
    bot.auto_mock_success = True
    assert 0 == await dao.level.count()

    await author_client.send("/" + NEW_LEVEL_COMMAND.command)
    first_message = message_manager.one_message()
    assert "Для начала дай уровню короткое описание (ID)" in first_message.text
    assert not first_message.reply_markup.inline_keyboard

    message_manager.reset_history()
    await author_client.send("test_level")
    new_message = message_manager.one_message()
    assert "test_level" in new_message.text
    assert "Отлично, перейдём к ключам" in new_message.text
    assert not new_message.reply_markup.inline_keyboard

    message_manager.reset_history()
    await author_client.send("SHTESTKEY")
    new_message = message_manager.one_message()
    assert "test_level" in new_message.text
    assert "Подсказки уровня" in new_message.text
    assert new_message.reply_markup.inline_keyboard

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator("Добавить подсказку"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert "Время выхода подсказки" in new_message.text
    assert "0" == new_message.reply_markup.inline_keyboard[1][0].text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator("0"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert "Подсказка выходящая в 0 мин." in new_message.text
    assert "Присылай сообщения" in new_message.text
    assert new_message.reply_markup.inline_keyboard

    message_manager.reset_history()
    await author_client.send("some hint text")
    new_message = message_manager.one_message()
    assert "Подсказка выходящая в 0 мин." in new_message.text
    assert "Можно прислать ещё сообщения" in new_message.text
    assert new_message.reply_markup.inline_keyboard

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator("К следующей подсказке"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert "test_level" in new_message.text
    assert "Подсказки уровня" in new_message.text
    assert "\n0: " in new_message.text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator("Добавить подсказку"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert "Время выхода подсказки" in new_message.text
    assert "5" == new_message.reply_markup.inline_keyboard[1][0].text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator("5"),
    )
    message_manager.assert_answered(callback_id)

    message_manager.reset_history()
    await author_client.send("SHTESTKEY")
    new_message = message_manager.one_message()
    assert "Подсказка выходящая в 5 мин." in new_message.text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator("К следующей подсказке"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert "test_level" in new_message.text
    assert "Подсказки уровня" in new_message.text
    assert "\n0: " in new_message.text
    assert "\n5: " in new_message.text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator("Готово, сохранить"),
    )
    message_manager.assert_answered(callback_id)
    request = bot.session.get_request()
    assert "Уровень успешно сохранён" == request.data["text"]

    assert 1 == await dao.level.count()
    level, *_ = await dao.level.get_all_my(author)
    level: dto.Level
    assert author.id == level.author.id
    assert {"SHTESTKEY"} == level.scenario.keys
    assert 2 == level.hints_count
    bot.auto_mock_success = False
