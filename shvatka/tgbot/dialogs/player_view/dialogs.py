from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Jinja, Const

from shvatka.tgbot import states
from .getters import player_getter

player_dialog = Dialog(
    Window(
        Jinja(
            "Игрок {{player.name_mention}}\n"
            "Введено корректных ключей / введено всего ключей (%) \n"
            "{{player.typed_correct_keys_count}} / {{player.typed_keys_count}} "
            "({{'%.2f'| format(correct_keys*100|float)}}%)"
            "\n\n"
            "{% if history %}"
            "{% for tp in history %}"
            "{{tp.date_joined | user_timezone}} -> {{tp.team.name}}"
            "{% if tp.date_left %} -> {{tp.date_left | user_timezone}}{% endif %} \n"
            "{% endfor %}"
            "{% endif %}"
        ),
        Cancel(Const("🔙Выход")),
        getter=player_getter,
        state=states.PlayerSg.main,
    ),
)
