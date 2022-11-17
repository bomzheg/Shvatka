from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const, Jinja

from tgbot.states import GamePublish
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
            "4. Перешли боту сообщение из канала с командой /publish"
        ),
        Cancel(Const("⤴Назад")),
        MessageInput(func=process_publish_message),
        state=GamePublish.prepare,
        getter=get_org,
    ),
)
