from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Select, SwitchTo, Url
from aiogram_dialog.widgets.text import Const, Format, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.paging import SmartScrollingGroup
from shvatka.tgbot.dialogs.preview_data import (
    PREVIEW_COMPOSE_DATA,
    PREVIEW_ORGS_DATA,
    PREVIEW_SEASON_DATA,
    PREVIEW_SLOT_DATA,
    PREVIEW_TAKE_DATA,
    PreviewSwitchTo,
)
from shvatka.tgbot.dialogs.season.calendar import SeasonCalendar

from .getters import get_compose, get_orgs, get_season, get_slot, get_take
from .handlers import (
    add_org,
    add_slot,
    as_player,
    as_team,
    cancel_compose,
    cancel_move,
    clear_orgs,
    next_year,
    pick_date,
    prev_year,
    publish_season,
    release_slot,
    remove_slot,
    save_orgs,
    start_compose,
    start_move,
    take_slot,
    to_confirm_publish,
    to_orgs,
    to_take,
    toggle_draft_date,
    unlink_game,
)

season = Dialog(
    Window(
        Jinja(
            "<b>Расписание сезона {{year}}</b>\n"
            "{% if moving %}"
            "Выбери день, на который перенести дату.\n"
            "{% endif %}"
            "{% if is_missing %}"
            "Расписание ещё не опубликовано.\n"
            "{% else %}"
            "🟢 свободна · 🔒 занята · ⭐ ваша · 🎮 с игрой\n"
            "{% for slot in season.slots %}"
            "{{ slot.date.strftime('%d.%m') }} — "
            "{% if slot.game %}{{ slot.game.name }}"
            "{% elif slot.author_name %}{{ slot.author_name }}"
            "{% else %}свободна{% endif %}"
            "{% if slot.note %} ({{ slot.note }}){% endif %}\n"
            "{% endfor %}"
            "{% endif %}"
        ),
        SeasonCalendar(id="season_calendar", on_click=pick_date),
        Button(
            Const("🚫Отменить перенос"),
            id="cancel_move",
            on_click=cancel_move,
            when=F["moving"],
        ),
        Button(Const("◀️Прошлый год"), id="prev_year", on_click=prev_year),
        Button(Const("Следующий год▶️"), id="next_year", on_click=next_year),
        Button(
            Const("📝Составить расписание"),
            id="compose",
            on_click=start_compose,
            when=F["can_compose"],
        ),
        Cancel(Const("🔙Назад")),
        state=states.SeasonSG.calendar,
        getter=get_season,
        preview_data=PREVIEW_SEASON_DATA,
        preview_add_transitions=[
            PreviewSwitchTo(states.SeasonSG.slot),
            PreviewSwitchTo(states.SeasonSG.compose),
        ],
    ),
    Window(
        Jinja(
            "{% if slot %}"
            "<b>Дата {{ slot.date.strftime('%d.%m.%Y') }}</b>\n"
            "{% if slot.game %}Игра: <b>{{ slot.game.name }}</b>\n{% endif %}"
            "{% if author_name %}Автор: {{ author_name }}\n"
            "{% else %}Дата свободна\n{% endif %}"
            "{% if orgs %}Орги: "
            "{% for org in orgs %}{{ org.name_mention }}{% if not loop.last %}, {% endif %}"
            "{% endfor %}\n{% endif %}"
            "{% if slot.note %}Заметка: {{ slot.note }}\n{% endif %}"
            "{% else %}"
            "<b>{{ picked_date }}</b> — в расписании нет такой даты.\n"
            "{% endif %}"
        ),
        Button(
            Const("➕Добавить дату"),
            id="add_slot",
            on_click=add_slot,
            when=~F["slot"] & F["is_author"],
        ),
        SwitchTo(
            Const("✋Взять дату"),
            id="to_take",
            state=states.SeasonSG.take,
            on_click=to_take,
            when=F["can_edit"] & F["is_free"],
        ),
        SwitchTo(
            Const("✏Сменить автора"),
            id="to_reassign",
            state=states.SeasonSG.take,
            on_click=to_take,
            when=F["can_edit"] & ~F["is_free"],
        ),
        SwitchTo(
            Const("👥Орги на дату"),
            id="to_orgs",
            state=states.SeasonSG.orgs,
            on_click=to_orgs,
            when=F["can_edit"] & F["slot"],
        ),
        Button(
            Const("↔Перенести дату"),
            id="start_move",
            on_click=start_move,
            when=F["can_edit"] & F["slot"],
        ),
        Url(
            Const("🎮Открыть игру"),
            Format("{game_url}"),
            when=F["slot"].game,
        ),
        Button(
            Const("🕊Освободить"),
            id="release_slot",
            on_click=release_slot,
            when=F["can_edit"] & ~F["is_free"],
        ),
        Button(
            Const("🎮Отвязать игру"),
            id="unlink_game",
            on_click=unlink_game,
            when=F["can_edit"] & F["slot"].game,
        ),
        Button(
            Const("🗑Удалить дату"),
            id="remove_slot",
            on_click=remove_slot,
            when=F["can_edit"] & F["slot"],
        ),
        SwitchTo(Const("🔙К календарю"), id="to_calendar", state=states.SeasonSG.calendar),
        state=states.SeasonSG.slot,
        getter=get_slot,
        preview_data=PREVIEW_SLOT_DATA,
        preview_add_transitions=[PreviewSwitchTo(states.SeasonSG.calendar)],
    ),
    Window(
        Jinja(
            "Кто будет автором игры на дату "
            "{% if slot %}{{ slot.date.strftime('%d.%m') }}{% else %}{{ picked_date }}{% endif %}?"
            "\n\nСейчас выбрано: "
            "{% if as_team %}команда{% else %}вы сами{% endif %}"
            "{% if any_team %}\n\nВам доступна любая команда — вы админ движка."
            "{% endif %}"
        ),
        Button(Const("🙋Я сам(а)"), id="as_player", on_click=as_player),
        SmartScrollingGroup(
            Select(
                Format("🚩{item.name}"),
                id="as_team",
                item_id_getter=lambda team: team.id,
                items="teams",
                on_click=as_team,
            ),
            id="teams_sg",
            width=1,
            height=8,
            when=F["has_teams"],
        ),
        Button(Const("✅Взять дату"), id="take_slot", on_click=take_slot),
        SwitchTo(Const("🔙Назад"), id="to_slot", state=states.SeasonSG.slot),
        state=states.SeasonSG.take,
        getter=get_take,
        preview_data=PREVIEW_TAKE_DATA,
    ),
    Window(
        Jinja(
            "Пришли username игрока, который будет оргом на эту дату.\n"
            "{% if has_orgs %}Сейчас в списке: "
            "{% for org in orgs %}{{ org.name_mention }}{% if not loop.last %}, {% endif %}"
            "{% endfor %}"
            "{% else %}Список пока пуст.{% endif %}"
        ),
        MessageInput(func=add_org),
        Button(
            Const("🧹Очистить список"), id="clear_orgs", on_click=clear_orgs, when=F["has_orgs"]
        ),
        Button(Const("💾Сохранить"), id="save_orgs", on_click=save_orgs),
        SwitchTo(Const("🔙Назад"), id="to_slot", state=states.SeasonSG.slot),
        state=states.SeasonSG.orgs,
        getter=get_orgs,
        preview_data=PREVIEW_ORGS_DATA,
    ),
    Window(
        Jinja(
            "<b>Расписание сезона {{year}}</b> — черновик\n"
            "Нажимай на дни, чтобы добавить или убрать дату. "
            "Пока расписание не опубликовано, ничего не сохраняется.\n\n"
            "{% if has_dates %}Выбрано {{ dates_count }}: "
            "{% for one in dates %}{{ one }}{% if not loop.last %}, {% endif %}{% endfor %}"
            "{% else %}Пока не выбрано ни одной даты.{% endif %}"
        ),
        SeasonCalendar(
            id="compose_calendar",
            on_click=toggle_draft_date,  # type: ignore[arg-type]
        ),
        Button(
            Const("📨Опубликовать"),
            id="to_confirm_publish",
            on_click=to_confirm_publish,
            when=F["has_dates"],
        ),
        Button(Const("❌Отменить"), id="cancel_compose", on_click=cancel_compose),
        state=states.SeasonSG.compose,
        getter=get_compose,
        preview_data=PREVIEW_COMPOSE_DATA,
        preview_add_transitions=[
            PreviewSwitchTo(states.SeasonSG.confirm_publish),
            PreviewSwitchTo(states.SeasonSG.calendar),
        ],
    ),
    Window(
        Jinja(
            "Опубликовать расписание сезона {{year}} из {{dates_count}} дат?\n"
            "{% for one in dates %}{{ one }}{% if not loop.last %}, {% endif %}{% endfor %}\n\n"
            "Об этом узнают все, кто играл или организовывал игры в последние два года."
        ),
        Button(Const("✅Опубликовать"), id="publish_season", on_click=publish_season),
        SwitchTo(Const("🔙Назад"), id="to_compose", state=states.SeasonSG.compose),
        state=states.SeasonSG.confirm_publish,
        getter=get_compose,
        preview_data=PREVIEW_COMPOSE_DATA,
        preview_add_transitions=[PreviewSwitchTo(states.SeasonSG.calendar)],
    ),
)
