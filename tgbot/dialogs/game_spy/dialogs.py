from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, SwitchTo, Cancel
from aiogram_dialog.widgets.text import Const, Format, Jinja, Multi

from tgbot.states import OrgSpy
from .getters import get_org, get_spy
from .handlers import keys_handler

game_spy = Dialog(
    Window(
        Multi(
            Jinja(
                "Шпион игры <b>{{game.name}}</b> с ID {{game.id}}\n"
                "Текущий статус: <b>{{game.status}}</b>\n"
                "Дата и время начала: "
            ),
            Jinja("{{ game.start_at|user_timezone }}", when=F["game"].start_at),
            Format("не запланирована", when=~F["game"].start_at),
            sep="",
        ),
        Cancel(Const("⤴Назад")),
        SwitchTo(
            Const("📊Текущие уровни"),
            id="spy_levels",
            state=OrgSpy.spy,
            when=F["org"].can_spy & F["game"].is_started,
        ),
        Button(
            Const("🔑Лог ключей"),
            id="spy_keys",
            on_click=keys_handler,
            when=F["game"].is_started & F["org"].can_see_log_keys,
        ),
        state=OrgSpy.main,
        getter=get_org,
    ),
    Window(
        Const("Актуальные сведения с полей схватки:"),
        Jinja(
            "{% for lt in stat %}"
            "{% if lt.is_finished %}"
            "<b>{{ lt.team.name }}</b> - финишировала в "
            "{% else %}"
            "<b>{{ lt.team.name }}</b> - уровень {{ lt.level_number + 1 }} начат "
            "{% endif %}"
            "{{ lt.start_at|user_timezone }}"
            "{% endfor %}",
            when=F["org"].can_spy,
        ),
        Button(Const("обновить"), id="refresh_spy"),
        SwitchTo(Const("Назад"), id="back", state=OrgSpy.main),
        state=OrgSpy.spy,
        getter=(get_spy, get_org),
    ),
)
