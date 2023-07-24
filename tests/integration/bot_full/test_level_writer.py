import pytest
from aiogram.enums import ContentType
from aiogram_dialog.test_tools import BotClient, MockMessageManager
from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator
from aiogram_tests.mocked_bot import MockedBot

from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.commands import NEW_LEVEL_COMMAND


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
    first_message = message_manager.last_message()
    assert first_message.text
    assert "Для начала дай уровню короткое описание (ID)" in first_message.text
    assert not first_message.reply_markup.inline_keyboard
    stub_msg = message_manager.first_message()
    assert stub_msg.content_type == ContentType.UNKNOWN

    message_manager.reset_history()
    await author_client.send("test_level")
    new_message = message_manager.one_message()
    assert new_message.text
    assert "Написание уровня test_level" in new_message.text
    assert "Ключи не введены" in new_message.text
    assert "Подсказки:\nпока нет ни одной" in new_message.text
    actual_kb = new_message.reply_markup.inline_keyboard
    assert "Ключи" in actual_kb[0][0].text
    assert "Подсказки" in actual_kb[1][0].text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator(".*Ключи"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert new_message.text
    assert "test_level" in new_message.text
    assert "Отлично, перейдём к ключам" in new_message.text
    assert "Назад" in new_message.reply_markup.inline_keyboard[0][0].text

    message_manager.reset_history()
    await author_client.send("SHTESTKEY")
    new_message = message_manager.one_message()
    assert new_message.text
    assert "Написание уровня test_level" in new_message.text
    assert "Ключей: 1" in new_message.text
    assert "Подсказки:\nпока нет ни одной" in new_message.text
    actual_kb = new_message.reply_markup.inline_keyboard
    assert "Ключи" in actual_kb[0][0].text
    assert "Подсказки" in actual_kb[1][0].text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator(".*Подсказки"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert new_message.text
    assert "Подсказки уровня test_level" in new_message.text
    assert "пока нет ни одной" in new_message.text
    assert "Добавить подсказку" in new_message.reply_markup.inline_keyboard[0][0].text
    assert "Назад" in new_message.reply_markup.inline_keyboard[1][0].text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator(".*Добавить подсказку"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert new_message.text
    assert "Подсказка выходящая в 0 мин." in new_message.text
    assert "Присылай сообщения" in new_message.text
    assert new_message.reply_markup.inline_keyboard

    message_manager.reset_history()
    await author_client.send("some hint text")
    new_message = message_manager.one_message()
    assert new_message.text
    assert "Подсказка выходящая в 0 мин." in new_message.text
    assert "Можно прислать ещё сообщения" in new_message.text
    assert new_message.reply_markup.inline_keyboard

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator(".*К следующей подсказке"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert new_message.text
    assert "test_level" in new_message.text
    assert "Подсказки уровня" in new_message.text
    assert "\n0: " in new_message.text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator(".*Добавить подсказку"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert new_message.text
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
    assert new_message.text
    assert "Подсказка выходящая в 5 мин." in new_message.text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator(".*К следующей подсказке"),
    )
    message_manager.assert_answered(callback_id)
    new_message = message_manager.one_message()
    assert new_message.text
    assert "test_level" in new_message.text
    assert "Подсказки уровня" in new_message.text
    assert "\n0: " in new_message.text
    assert "\n5: " in new_message.text

    message_manager.reset_history()
    callback_id = await author_client.click(
        new_message,
        InlineButtonTextLocator(".*Достаточно подсказок"),
    )
    message_manager.assert_answered(callback_id)
    msg = message_manager.one_message()
    assert "Готово, сохранить" in msg.reply_markup.inline_keyboard[2][0].text

    message_manager.reset_history()
    callback_id = await author_client.click(
        msg,
        InlineButtonTextLocator(".*Готово, сохранить"),
    )
    message_manager.assert_answered(callback_id)
    request = bot.session.get_request()
    assert "Уровень успешно сохранён" == request.data["text"]
    assert 1 == await dao.level.count()
    level, *_ = await dao.level.get_all_my(author)
    assert author.id == level.author.id
    assert {"SHTESTKEY"} == level.scenario.keys
    assert 2 == level.hints_count
    bot.auto_mock_success = False
