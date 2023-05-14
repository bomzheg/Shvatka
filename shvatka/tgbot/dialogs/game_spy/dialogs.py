from datetime import datetime

from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, SwitchTo, Cancel
from aiogram_dialog.widgets.text import Const, Format, Jinja, Multi

from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.tgbot import states
from .getters import get_org, get_spy, get_keys
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
        Cancel(Const("🔙Назад")),
        SwitchTo(
            Const("📊Текущие уровни"),
            id="spy_levels",
            state=states.OrgSpySG.spy,
            when=F["org"].can_spy & F["game"].is_started,
        ),
        SwitchTo(
            Const("🔑Лог ключей"),
            id="spy_keys",
            state=states.OrgSpySG.keys,
            when=F["game"].is_started & F["org"].can_see_log_keys,
        ),
        state=states.OrgSpySG.main,
        getter=get_org,
    ),
    Window(
        Const("Актуальные сведения с полей схватки:"),
        Jinja(
            "{% for lt in stat %}"
            "{% if lt.is_finished %}"
            "🏁<b>{{ lt.team.name }}</b> - финишировала в "
            "{% else %}"
            "🚩<b>{{ lt.team.name }}</b> - уровень {{ lt.level_number + 1 }} начат "
            "{% endif %}"
            "{{ lt.start_at|user_timezone }}\n"
            "{% endfor %}",
            when=F["org"].can_spy,
        ),
        Button(Const("🔄Обновить"), id="refresh_spy"),
        SwitchTo(Const("🔙Назад"), id="back", state=states.OrgSpySG.main),
        state=states.OrgSpySG.spy,
        getter=(get_spy, get_org),
    ),
    Window(
        Jinja(
            "Промежуточный лог ключей \n"
            "для игры <b>{{game.name}}</b> "
            "(началась в {{game.start_at|user_timezone}}) \n"
            "по состоянию на {{ now | user_timezone }}\n"
            "{% if key_link %}"
            'доступен <a href="{{key_link}}">по ссылке</a>'
            "{% else %}"
            "пока недоступен (попробуй обновить)"
            "{% endif %}"
        ),
        Button(Const("🔄Обновить"), id="refresh_spy", on_click=keys_handler),
        SwitchTo(Const("🔙Назад"), id="back", state=states.OrgSpySG.main),
        state=states.OrgSpySG.keys,
        getter=(get_org, get_keys, {"now": datetime.now(tz=tz_utc)}),
        disable_web_page_preview=True,
    ),
)
