from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format, Jinja, Multi

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

LEGEND = Const("\n🟢 свободна · 🔒 занята · ⭐ твоя · 🎮 с игрой")

season = Dialog(
    Window(
        Multi(Format("{season_text}"), LEGEND, when=F["has_season"]),
        Multi(
            Format("{season_text}"),
            Const("\nЛюбой автор может составить его и опубликовать."),
            when=~F["has_season"],
        ),
        SeasonCalendar(
            id="season_calendar",
            on_click=select_day,  # type: ignore[arg-type]
            config=SEASON_CALENDAR_CONFIG,
            when=F["has_season"],
        ),
        Button(
            Format("📝Составить расписание {year}"),
            id="compose_season",
            on_click=start_compose,
            when=~F["has_season"] & F["can_edit"],
        ),
        Button(Format("◀️{prev_year}"), id="prev_year", on_click=to_prev_year),
        Button(Format("{next_year}▶️"), id="next_year", on_click=to_next_year),
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
        Multi(
            Jinja("<b>{{day_title}}</b>"),
            Format("{slot_text}", when=F["slot"]),
            Format("{nothing_planed}", when=~F["slot"]),
            sep="\n",
        ),
        SmartScrollingGroup(
            Select(
                Format("{item.slot_date:%d.%m} #{item.id}"),
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
                Format("🚩{item.name}"),
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
        Multi(
            Jinja("Орги на дату <b>{{day_title}}</b>"),
            Format("{slot_text}"),
            Const("\nПришли имя или @username, чтобы найти игрока"),
            sep="\n",
        ),
        MessageInput(func=search_orgs),
        SmartScrollingGroup(
            Select(
                Format("➕{item.name_mention}"),
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
                Format("🗑{item.name_mention}"),
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
        Multi(
            Jinja("Удалить дату <b>{{day_title}}</b> из расписания?"),
            Format("{slot_text}"),
            Const("\nЭто изменение попадёт в сводку и увидят все."),
            sep="\n",
        ),
        Button(Const("🗑Удалить"), id="remove_slot", on_click=remove_slot),
        SwitchTo(Const("❌Отменить"), id="to_slot", state=states.SeasonSG.slot),
        state=states.SeasonSG.confirm_delete,
        getter=get_slot,
        preview_data=PREVIEW_SEASON_SLOT,
        preview_add_transitions=[PreviewSwitchTo(states.SeasonSG.calendar)],
    ),
    Window(
        Multi(
            Jinja("Составляем расписание сезона <b>{{year}}</b>. Дат: {{count}}"),
            Format("{days_text}", when=F["has_days"]),
            Const("Отметь дни игр на календаре"),
            sep="\n",
        ),
        SeasonCalendar(
            id="compose_calendar",
            on_click=toggle_compose_day,  # type: ignore[arg-type]
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
        Multi(
            Jinja("Опубликовать расписание сезона <b>{{year}}</b>?"),
            Format("{days_text}"),
            Const("\nОб этом узнают все, кто играл или организовывал в этом сезоне."),
            sep="\n",
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
