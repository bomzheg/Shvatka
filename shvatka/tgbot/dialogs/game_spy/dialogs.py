from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, SwitchTo
from aiogram_dialog.widgets.text import Const, Jinja, Multi

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.preview_data import (
    PREVIEW_FINISHED_LEVEL_TIME,
    PREVIEW_NOW,
    PREVIEW_SPY_ORG,
    PREVIEW_SPY_STAT,
)

from .getters import get_keys, get_org, get_spy
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
            Const("не запланирована", when=~F["game"].start_at),
            sep="",
        ),
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
        Cancel(Const("🔙Назад")),
        state=states.OrgSpySG.main,
        getter=get_org,
        preview_data=PREVIEW_SPY_ORG,
    ),
    Window(
        Const("Актуальные сведения с полей схватки:"),
        Jinja(
            "{% for lt in finished %}"
            "🏁<b>{{ lt.team.name }}</b> - финишировала в "
            "{{ lt.start_at|time_user_timezone }} ({{(now - lt.start_at) | timedelta}} назад)\n"
            "{% endfor %}"
            "{% for i, lts in stat.items() %}"
            "<b><u>Уровень {{ i + 1 }}</u></b>\n"
            "{% for lt in lts %}"
            "🚩<b>{{ lt.team.name }}</b> - начат в "
            "{{ lt.start_at|time_user_timezone }} ({{(now - lt.start_at) | timedelta}} назад)\n"
            "Подсказка №{{lt.hint.number}} — {{lt.hint.time}} мин.\n"
            "{% endfor %}"
            "{% endfor %}",
            when=F["org"].can_spy,
        ),
        Button(Const("🔄Обновить"), id="refresh_spy"),
        SwitchTo(Const("🔙Назад"), id="back", state=states.OrgSpySG.main),
        state=states.OrgSpySG.spy,
        getter=(get_spy, get_org),
        preview_data={
            **PREVIEW_SPY_ORG,
            "stat": PREVIEW_SPY_STAT,
            "finished": [PREVIEW_FINISHED_LEVEL_TIME],
            "now": PREVIEW_NOW,
        },
    ),
    Window(
        Jinja(
            "Промежуточный лог ключей \n"
            "для игры <b>{{game.name}}</b> "
            "(началась в {{game.start_at|user_timezone}}) \n"
            "{% if key_link %}"
            'доступен <a href="{{key_link}}">по ссылке</a>\n'
            "по состоянию на {{ updated | user_timezone }}"
            "{% else %}"
            "пока недоступен (попробуй обновить)"
            "{% endif %}"
        ),
        Button(Const("🔄Обновить"), id="refresh_spy", on_click=keys_handler),
        SwitchTo(Const("🔙Назад"), id="back", state=states.OrgSpySG.main),
        state=states.OrgSpySG.keys,
        getter=(get_org, get_keys),
        preview_data={
            **PREVIEW_SPY_ORG,
            "key_link": "https://telegra.ph/keys",
            "updated": PREVIEW_NOW,
        },
        disable_web_page_preview=True,
    ),
)
