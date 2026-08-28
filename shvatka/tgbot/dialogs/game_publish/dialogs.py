from aiogram import F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel
from aiogram_dialog.widgets.text import Const, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.game_manage.handlers import publish_game_forum
from shvatka.tgbot.dialogs.preview_data import PREVIEW_AUTHOR, PREVIEW_SIMPLE_GAME

from .getters import get_org
from .handlers import process_publish_message

game_publish = Dialog(
    Window(
        Jinja(
            "Публикация игры <b>{{game.name}}</b> с ID {{game.id}}\n"
            "Текущий статус: <b>{{game.status}}</b>\n"
            "Дата и время начала: {{game.start_at|user_timezone}}\n\n"
            "Для публикации сценария игры:\n"
            "1. Создай приватный канал\n"
            "2. Добавь в него бота с правами администратора\n"
            "3. Отправь в канал команду /publish\n"
            "4. Перешли боту сообщение из канала с командой /publish",
            when=~F["started"] & ~F["started_at"],
        ),
        Jinja(
            "Игра {{game.name}} находится в процессе публикации. "
            "Публикация начата в {{started_at|user_timezone}}",
            when=F["started"],
        ),
        Jinja(
            "Игра {{game.name}} опубликована.\n{{text_invite}}",
            when=F["text_invite"],
        ),
        Button(Const("🔄Обновить"), id="refresh_publish", when=F["started"]),
        Cancel(Const("🔙Назад")),
        MessageInput(func=process_publish_message, filter=Command("publish")),
        state=states.GamePublishSG.prepare,
        getter=get_org,
        preview_data={
            "game": PREVIEW_SIMPLE_GAME,
            "player": PREVIEW_AUTHOR,
            "started": False,
            "started_at": None,
            "text_invite": None,
        },
    ),
    Window(
        Jinja(
            "Пришли логин и пароль от форума схватки.\n"
            "В первой строке логин, во второй пароль.\n"
            "Например:\n\n"
            "cool player name\n"
            "mY secure pas$w0rd"
        ),
        MessageInput(func=publish_game_forum, content_types=ContentType.TEXT),
        state=states.GamePublishSG.forum,
    ),
)
