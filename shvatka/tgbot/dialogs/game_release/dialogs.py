from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, SwitchTo
from aiogram_dialog.widgets.text import Case, Const, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.preview_data import PREVIEW_GAME, PreviewSwitchTo
from .getters import get_composed_release, get_release
from .handlers import (
    delete_release,
    drop_banner,
    preview_release,
    process_banner,
    process_release_message,
    reset_composed_release,
    save_release,
    show_release,
    to_compose_release,
)

game_release = Dialog(
    Window(
        Jinja(
            "Релиз игры <b>{{game.name}}</b>\n"
            "{% if not has_release %}"
            "Релиза пока нет. Это необязательно — игра прекрасно пройдёт и без него.\n"
            "Обычно релиз — это баннер с подписью, описание темы и карта района.\n"
            "{% else %}"
            "{% if is_published %}Опубликован в канале:{% else %}"
            "Сохранён, уйдёт в канал вместе с началом сбора вейверов:{% endif %}\n"
            "{% if banner %}🖼{{banner | single_hint}}\n{% endif %}"
            "{{hints | hints}}\n"
            "{% if is_published %}Если изменить — сообщения в канале обновятся.{% endif %}"
            "{% endif %}"
        ),
        Button(
            Const("📝Собрать релиз"),
            id="compose_release",
            on_click=to_compose_release,
        ),
        Button(
            Const("👁Показать"),
            id="show_release",
            on_click=show_release,
            when=F["has_release"],
        ),
        Button(
            Const("🗑Удалить релиз"),
            id="delete_release",
            on_click=delete_release,
            when=F["has_release"],
        ),
        Cancel(Const("🔙Назад")),
        state=states.GameReleaseSG.menu,
        getter=get_release,
        preview_data={
            "game": PREVIEW_GAME,
            "has_release": True,
            "is_published": True,
            "banner": None,
        },
        preview_add_transitions=[PreviewSwitchTo(states.GameReleaseSG.banner)],
    ),
    Window(
        Case(
            {
                False: Const(
                    "Пришли баннер — картинку, с которой начнётся релиз, "
                    "можно сразу с подписью.\n"
                    "Обычно это широкая картинка (примерно 1280×250—1280×550): "
                    "именно её увидят на сайте над шапкой.\n"
                    "Баннер необязателен — можно сразу перейти к остальному."
                ),
                True: Jinja(
                    "Баннер:\n{{banner | single_hint}}\n"
                    "Можно прислать другую картинку или идти дальше."
                ),
            },
            selector="has_banner",
        ),
        MessageInput(func=process_banner),
        SwitchTo(
            Const("➡️Дальше"),
            id="to_compose",
            state=states.GameReleaseSG.compose,
        ),
        Button(
            Const("🚫Без баннера"),
            id="drop_banner",
            on_click=drop_banner,
            when=F["has_banner"],
        ),
        SwitchTo(Const("🔙Назад"), id="to_release_menu", state=states.GameReleaseSG.menu),
        state=states.GameReleaseSG.banner,
        getter=get_composed_release,
        preview_data={"has_banner": False},
        preview_add_transitions=[PreviewSwitchTo(states.GameReleaseSG.compose)],
    ),
    Window(
        Case(
            {
                False: Const(
                    "Присылай остальные сообщения релиза (текст про тему, карта, что угодно). "
                    "Они будут опубликованы именно в таком виде и порядке — после баннера."
                ),
                True: Jinja(
                    "{{hints | hints}}\nМожно прислать ещё сообщения или перейти к предпросмотру"
                ),
            },
            selector="has_hints",
        ),
        MessageInput(func=process_release_message),
        Button(
            Const("👁Предпросмотр"),
            id="preview_release",
            on_click=preview_release,
            when=~F["is_empty"],
        ),
        Button(
            Const("♻️Начать заново"),
            id="reset_release",
            on_click=reset_composed_release,
            when=F["has_hints"],
        ),
        SwitchTo(
            Const("🖼К баннеру"),
            id="to_banner",
            state=states.GameReleaseSG.banner,
        ),
        SwitchTo(Const("🔙Назад"), id="to_release_menu", state=states.GameReleaseSG.menu),
        state=states.GameReleaseSG.compose,
        getter=get_composed_release,
        preview_data={"has_hints": True, "is_empty": False},
        preview_add_transitions=[PreviewSwitchTo(states.GameReleaseSG.confirm)],
    ),
    Window(
        Jinja(
            "{% if is_published %}"
            "Так релиз будет выглядеть после правки — сообщения в канале обновятся."
            "{% elif waits_for_waivers %}"
            "Так релиз увидят все. Он уйдёт в канал, когда начнётся сбор вейверов."
            "{% elif late %}"
            "Так релиз увидят на сайте. Игра уже началась, поэтому в канал он не пойдёт."
            "{% else %}"
            "Так релиз увидят все — он сразу уйдёт в канал."
            "{% endif %}"
        ),
        Button(
            Const("✅Сохранить"),
            id="save_release",
            on_click=save_release,
        ),
        SwitchTo(
            Const("✏Дописать"),
            id="back_to_compose",
            state=states.GameReleaseSG.compose,
        ),
        SwitchTo(Const("🔙Назад"), id="to_release_menu", state=states.GameReleaseSG.menu),
        state=states.GameReleaseSG.confirm,
        getter=get_release,
        preview_data={
            "game": PREVIEW_GAME,
            "is_published": False,
            "waits_for_waivers": True,
        },
    ),
)
