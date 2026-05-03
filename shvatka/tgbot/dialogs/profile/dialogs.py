from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Cancel, SwitchTo
from aiogram_dialog.widgets.text import Const, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.profile.getters import player_getter, player_stat_getter
from shvatka.tgbot.dialogs.profile.handlers import save_new_username

profile_dialog = Dialog(
    Window(
        Jinja(
            "Игрок {{player.name_mention}} ({{palyer.id}})\n"
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
        SwitchTo(
            Const("Изменить username"),
            state=states.ProfileSG.username,
            id="to_change_username",
        ),
        Cancel(Const("🔙Выход")),
        state=states.ProfileSG.main,
        getter=player_stat_getter,
    ),
    Window(
        Jinja("Введи своё новое имя пользователя. Сейчас сохранено {{player.username}}"),
        TextInput(
            id="get_new_username",
            on_success=save_new_username,
        ),
        state=states.ProfileSG.username,
        getter=player_getter,
    ),
)
