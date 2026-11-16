from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Jinja

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.paging import SmartScrollingGroup
from shvatka.tgbot.dialogs.preview_data import (
    PREVIEW_SEASON_CALENDAR,
    PREVIEW_SEASON_COMPOSE,
    PREVIEW_SEASON_MOVE,
    PREVIEW_SEASON_ORGS,
    PREVIEW_SEASON_SLOT,
    PREVIEW_SEASON_TAKE,
    PreviewStart,
    PreviewSwitchTo,
)

from .calendar import SEASON_CALENDAR_CONFIG, SeasonCalendar
from .getters import get_calendar, get_compose, get_move, get_orgs, get_slot, get_take
from .handlers import (
    add_org,
    add_slot,
    move_slot,
    on_season_start,
    open_linked_game,
    publish_season,
    release_slot,
    remove_org,
    remove_slot,
    reset_compose,
    search_orgs,
    select_day,
    select_day_slot,
    start_compose,
    take_as_player,
    take_as_team,
    to_next_year,
    to_prev_year,
    toggle_compose_day,
    unlink_game,
)

season = Dialog(
    Window(
        Jinja(
            "{{season_text|safe}}\n\n🟢 свободна · 🔒 занята · ⭐ твоя · 🎮 с игрой"
            "{% if not has_season %}\n\nЛюбой автор может составить его и опубликовать.{% endif %}"
        ),
        SeasonCalendar(
            id="season_calendar",
            on_click=select_day,
            config=SEASON_CALENDAR_CONFIG,
            when=F["has_season"],
        ),
        Button(
            Jinja("📝Составить расписание {{year}}"),
            id="compose_season",
            on_click=start_compose,
            when=~F["has_season"] & F["can_edit"],
        ),
        Button(Jinja("◀️{{prev_year}}"), id="prev_year", on_click=to_prev_year),
        Button(Jinja("{{next_year}}▶️"), id="next_year", on_click=to_next_year),
        Cancel(Const("🔙Назад")),
        state=states.SeasonSG.calendar,
        getter=get_calendar,
        preview_data=PREVIEW_SEASON_CALENDAR,
        preview_add_transitions=[
            PreviewSwitchTo(states.SeasonSG.slot),
            PreviewSwitchTo(states.SeasonSG.compose),
        ],
    ),
    Window(
        Jinja(
            "<b>{{day_title}}</b>\n"
            "{% if slot %}{{slot_text|safe}}"
            "{% else %}На {{day_title}} в расписании сезона ничего не запланировано{% endif %}"
        ),
        SmartScrollingGroup(
            Select(
                Jinja("{{item.slot_date|user_date('%d.%m')}} #{{item.id}}"),
                id="day_slots",
                item_id_getter=lambda slot: slot.id,
                items="day_slots",
                on_click=select_day_slot,
            ),
            id="day_slots_sg",
            width=2,
            height=3,
            when=F["has_many"],
        ),
        Button(
            Const("➕Добавить дату"),
            id="add_slot",
            on_click=add_slot,
            when=~F["slot"] & F["can_edit"],
        ),
        SwitchTo(
            Const("🖐Взять дату"),
            id="to_take",
            state=states.SeasonSG.take,
            when=F["is_free"] & F["can_edit"],
        ),
        SwitchTo(
            Const("♻️Сменить автора"),
            id="to_retake",
            state=states.SeasonSG.take,
            when=F["is_taken"] & F["can_edit"],
        ),
        SwitchTo(
            Const("👥Орги на дату"),
            id="to_orgs",
            state=states.SeasonSG.orgs,
            when=F["is_taken"] & F["can_edit"],
        ),
        Button(
            Const("🙌Освободить дату"),
            id="release_slot",
            on_click=release_slot,
            when=F["can_release"] & F["can_edit"],
        ),
        Button(
            Const("🎮Открыть игру"),
            id="open_game",
            on_click=open_linked_game,
            when=F["is_my_game"],
        ),
        Button(
            Const("🔓Отвязать игру"),
            id="unlink_game",
            on_click=unlink_game,
            when=F["is_linked"] & F["can_edit"],
        ),
        SwitchTo(
            Const("📆Перенести"),
            id="to_move",
            state=states.SeasonSG.move,
            when=F["slot"] & F["can_edit"],
        ),
        SwitchTo(
            Const("🗑Удалить дату"),
            id="to_delete",
            state=states.SeasonSG.confirm_delete,
            when=F["slot"] & F["can_edit"],
        ),
        SwitchTo(Const("🔙К расписанию"), id="to_calendar", state=states.SeasonSG.calendar),
        state=states.SeasonSG.slot,
        getter=get_slot,
        preview_data=PREVIEW_SEASON_SLOT,
        preview_add_transitions=[PreviewStart(states.MyGamesPanelSG.game_menu)],
    ),
    Window(
        Jinja(
            "Кто будет автором игры на <b>{{day_title}}</b>?\n"
            "{% if author %}Сейчас дата записана на <b>{{author}}</b>.{% endif %}"
        ),
        Button(Const("👤Я сам"), id="take_as_player", on_click=take_as_player),
        SmartScrollingGroup(
            Select(
                Jinja("🚩{{item.name}}"),
                id="take_teams",
                item_id_getter=lambda team: team.id,
                items="teams",
                on_click=take_as_team,
            ),
            id="take_teams_sg",
            width=1,
            height=5,
            when=F["has_teams"],
        ),
        Const(
            "Записать команду на дату может только её капитан",
            when=~F["has_teams"],
        ),
        SwitchTo(Const("🔙Назад"), id="to_slot", state=states.SeasonSG.slot),
        state=states.SeasonSG.take,
        getter=get_take,
        preview_data=PREVIEW_SEASON_TAKE,
    ),
    Window(
        Jinja(
            "Орги на дату <b>{{day_title}}</b>\n{{slot_text|safe}}\n\n"
            "Пришли имя или @username, чтобы найти игрока"
        ),
        MessageInput(func=search_orgs),
        SmartScrollingGroup(
            Select(
                Jinja("➕{{item.name_mention}}"),
                id="found_orgs",
                item_id_getter=lambda player: player.id,
                items="found",
                on_click=add_org,
            ),
            id="found_orgs_sg",
            width=1,
            height=5,
            when=F["has_found"],
        ),
        SmartScrollingGroup(
            Select(
                Jinja("🗑{{item.name_mention}}"),
                id="slot_orgs",
                item_id_getter=lambda player: player.id,
                items="orgs",
                on_click=remove_org,
            ),
            id="slot_orgs_sg",
            width=1,
            height=5,
        ),
        SwitchTo(Const("🔙Назад"), id="to_slot", state=states.SeasonSG.slot),
        state=states.SeasonSG.orgs,
        getter=get_orgs,
        preview_data=PREVIEW_SEASON_ORGS,
    ),
    Window(
        Jinja("Куда перенести дату <b>{{day_title}}</b>? Выбери новый день сезона {{year}}"),
        SeasonCalendar(
            id="move_calendar",
            on_click=move_slot,
            config=SEASON_CALENDAR_CONFIG,
        ),
        SwitchTo(Const("🔙Назад"), id="to_slot", state=states.SeasonSG.slot),
        state=states.SeasonSG.move,
        getter=get_move,
        preview_data=PREVIEW_SEASON_MOVE,
        preview_add_transitions=[PreviewSwitchTo(states.SeasonSG.slot)],
    ),
    Window(
        Jinja(
            "Удалить дату <b>{{day_title}}</b> из расписания?\n{{slot_text|safe}}\n\n"
            "Это изменение попадёт в сводку и увидят все."
        ),
        Button(Const("🗑Удалить"), id="remove_slot", on_click=remove_slot),
        SwitchTo(Const("❌Отменить"), id="to_slot", state=states.SeasonSG.slot),
        state=states.SeasonSG.confirm_delete,
        getter=get_slot,
        preview_data=PREVIEW_SEASON_SLOT,
        preview_add_transitions=[PreviewSwitchTo(states.SeasonSG.calendar)],
    ),
    Window(
        Jinja(
            "Составляем расписание сезона <b>{{year}}</b>. Дат: {{count}}\n"
            "{% if has_days %}{{days_text}}\n{% endif %}Отметь дни игр на календаре"
        ),
        SeasonCalendar(
            id="compose_calendar",
            on_click=toggle_compose_day,
            config=SEASON_CALENDAR_CONFIG,
        ),
        Button(Const("♻️Вернуть даты по умолчанию"), id="reset_compose", on_click=reset_compose),
        SwitchTo(
            Const("✅Опубликовать"),
            id="to_confirm_publish",
            state=states.SeasonSG.confirm_publish,
            when=F["has_days"],
        ),
        SwitchTo(Const("🔙Назад"), id="to_calendar", state=states.SeasonSG.calendar),
        state=states.SeasonSG.compose,
        getter=get_compose,
        preview_data=PREVIEW_SEASON_COMPOSE,
    ),
    Window(
        Jinja(
            "Опубликовать расписание сезона <b>{{year}}</b>?\n{{days_text}}\n\n"
            "Об этом узнают все, кто играл или организовывал в этом сезоне."
        ),
        Button(Const("✅Опубликовать"), id="publish_season", on_click=publish_season),
        SwitchTo(Const("🔙Назад"), id="to_compose", state=states.SeasonSG.compose),
        state=states.SeasonSG.confirm_publish,
        getter=get_compose,
        preview_data=PREVIEW_SEASON_COMPOSE,
        preview_add_transitions=[PreviewSwitchTo(states.SeasonSG.calendar)],
    ),
    on_start=on_season_start,
)
