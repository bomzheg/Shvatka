from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Cancel, SwitchTo, Url
from aiogram_dialog.widgets.text import Const, Format, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.preview_data import (
    PREVIEW_AUTHOR,
    PREVIEW_PLAYER_STAT,
    PreviewSwitchTo,
)
from shvatka.tgbot.dialogs.profile.getters import (
    player_getter,
    player_one_time_url_getter,
    player_stat_getter,
)
from shvatka.tgbot.dialogs.profile.handlers import (
    email_invalid,
    on_email_code_entered,
    on_email_entered,
    save_new_username,
    username_invalid,
    validate_email_input,
    validate_username,
)

profile_dialog = Dialog(
    Window(
        Jinja(
            "Игрок {{player.name_mention}} ({{player.id}})\n"
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
        SwitchTo(
            Const("Быстрый вход"),
            state=states.ProfileSG.one_time_login,
            id="to_ott",
        ),
        SwitchTo(
            Const("Привязать email"),
            state=states.ProfileSG.email,
            id="to_email",
        ),
        Cancel(Const("🔙Выход")),
        state=states.ProfileSG.main,
        getter=player_stat_getter,
        preview_data=PREVIEW_PLAYER_STAT,
    ),
    Window(
        Const("Введи адрес электронной почты, который хочешь привязать к аккаунту"),
        SwitchTo(
            Const("🔙Назад"),
            state=states.ProfileSG.main,
            id="email_to_main",
        ),
        TextInput(
            id="get_email",
            type_factory=validate_email_input,
            on_success=on_email_entered,
            on_error=email_invalid,
        ),
        state=states.ProfileSG.email,
        preview_add_transitions=[PreviewSwitchTo(states.ProfileSG.email_code)],
    ),
    Window(
        Const("Введи код подтверждения, отправленный на указанную почту"),
        SwitchTo(
            Const("🔙Назад"),
            state=states.ProfileSG.main,
            id="email_code_to_main",
        ),
        TextInput(
            id="get_email_code",
            type_factory=str,
            on_success=on_email_code_entered,
        ),
        state=states.ProfileSG.email_code,
        # back to the address input when someone else took the email meanwhile
        preview_add_transitions=[PreviewSwitchTo(states.ProfileSG.email)],
    ),
    Window(
        Jinja("Введи своё новое имя пользователя. Сейчас сохранено {{player.username}}"),
        SwitchTo(
            Const("🔙Назад"),
            state=states.ProfileSG.main,
            id="to_main",
        ),
        TextInput(
            id="get_new_username",
            type_factory=validate_username,
            on_success=save_new_username,
            on_error=username_invalid,
        ),
        state=states.ProfileSG.username,
        getter=player_getter,
        preview_data={"player": PREVIEW_AUTHOR},
    ),
    Window(
        Jinja("{{player.username}}\nДля входа нажми на кнопку ниже"),
        Url(
            text=Const("Войти"),
            url=Format("{url}"),
        ),
        SwitchTo(
            Const("🔙Назад"),
            state=states.ProfileSG.main,
            id="to_main",
        ),
        state=states.ProfileSG.one_time_login,
        getter=(player_getter, player_one_time_url_getter),
        preview_data={"player": PREVIEW_AUTHOR, "url": "https://shvatka.ru/login?token=1"},
    ),
)
