from __future__ import annotations

from datetime import date, datetime
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.season import dto
from shvatka.core.season.interactors import (
    AddSlotInteractor,
    GetDefaultSlotDatesInteractor,
    GetSeasonInteractor,
    MoveSlotInteractor,
    PublishSeasonInteractor,
    ReleaseSlotInteractor,
    RemoveSlotInteractor,
    SetSlotOrgsInteractor,
    TakeSlotInteractor,
    UnlinkGameFromSlotInteractor,
)
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.tgbot import states
from shvatka.tgbot.dialogs.season.getters import (
    COMPOSE_KEY,
    FOUND_KEY,
    SLOT_DATE_KEY,
    SLOT_ID_KEY,
    YEAR_KEY,
    compose_dates,
    current_year,
    pick_slot,
    require_slot,
    season_or_none,
    sorted_slots,
)


async def on_season_start(start_data: Any, manager: DialogManager) -> None:
    data = start_data if isinstance(start_data, dict) else {}
    manager.dialog_data[YEAR_KEY] = int(data.get(YEAR_KEY) or datetime.now(tz=tz_game).year)


async def _slot(manager: DialogManager, reader: GetSeasonInteractor) -> dto.Slot:
    slots = sorted_slots(await season_or_none(reader, current_year(manager)))
    return require_slot(pick_slot(manager, slots))


def _show_slot(manager: DialogManager, slot: dto.Slot) -> None:
    manager.dialog_data[SLOT_DATE_KEY] = slot.slot_date.isoformat()
    manager.dialog_data[SLOT_ID_KEY] = slot.id


def _switch_year(manager: DialogManager, year: int) -> None:
    manager.dialog_data[YEAR_KEY] = year
    # the season is another one now, so nothing chosen in the old one survives
    for key in (SLOT_DATE_KEY, SLOT_ID_KEY, COMPOSE_KEY, FOUND_KEY):
        manager.dialog_data.pop(key, None)


async def to_prev_year(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    _switch_year(manager, current_year(manager) - 1)


async def to_next_year(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    _switch_year(manager, current_year(manager) + 1)


async def select_day(c: CallbackQuery, widget: Any, manager: DialogManager, day: date) -> None:
    # a tap never writes: it opens the window that offers what may be done
    manager.dialog_data[SLOT_DATE_KEY] = day.isoformat()
    manager.dialog_data.pop(SLOT_ID_KEY, None)
    await manager.switch_to(states.SeasonSG.slot)


async def select_day_slot(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data[SLOT_ID_KEY] = int(item_id)


@inject
async def add_slot(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[AddSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    year = current_year(manager)
    day = date.fromisoformat(manager.dialog_data[SLOT_DATE_KEY])
    slot = await interactor(year, day, None, identity=identity)
    _show_slot(manager, slot)


@inject
async def take_as_player(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[TakeSlotInteractor],
    reader: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    slot = await _slot(manager, reader)
    await interactor(
        current_year(manager),
        slot.id,
        author_kind=dto.SlotAuthorKind.player,
        team_id=None,
        # re-taking to change the author must not drop the people already named
        org_player_ids=[org.id for org in slot.orgs],
        identity=identity,
    )
    await manager.switch_to(states.SeasonSG.slot)


@inject
async def take_as_team(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
    interactor: FromDishka[TakeSlotInteractor],
    reader: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    slot = await _slot(manager, reader)
    await interactor(
        current_year(manager),
        slot.id,
        author_kind=dto.SlotAuthorKind.team,
        team_id=int(item_id),
        org_player_ids=[org.id for org in slot.orgs],
        identity=identity,
    )
    await manager.switch_to(states.SeasonSG.slot)


@inject
async def release_slot(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[ReleaseSlotInteractor],
    reader: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    slot = await _slot(manager, reader)
    await interactor(current_year(manager), slot.id, identity=identity)


@inject
async def unlink_game(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[UnlinkGameFromSlotInteractor],
    reader: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    slot = await _slot(manager, reader)
    await interactor(current_year(manager), slot.id, identity=identity)


@inject
async def open_linked_game(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    reader: FromDishka[GetSeasonInteractor],
) -> None:
    slot = await _slot(manager, reader)
    if slot.game is None:
        return
    await manager.start(states.MyGamesPanelSG.game_menu, data={"my_game_id": slot.game.id})


@inject
async def move_slot(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    day: date,
    interactor: FromDishka[MoveSlotInteractor],
    reader: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    slot = await _slot(manager, reader)
    moved = await interactor(current_year(manager), slot.id, day, identity=identity)
    _show_slot(manager, moved)
    await manager.switch_to(states.SeasonSG.slot)


@inject
async def remove_slot(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[RemoveSlotInteractor],
    reader: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    slot = await _slot(manager, reader)
    await interactor(current_year(manager), slot.id, identity=identity)
    manager.dialog_data.pop(SLOT_ID_KEY, None)
    await manager.switch_to(states.SeasonSG.calendar)


async def search_orgs(m: Message, widget: Any, manager: DialogManager) -> None:
    # the window shows the matches; picking one is what writes
    assert m.text
    manager.dialog_data[FOUND_KEY] = m.text.strip()


@inject
async def add_org(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
    interactor: FromDishka[SetSlotOrgsInteractor],
    reader: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    slot = await _slot(manager, reader)
    await interactor(
        current_year(manager),
        slot.id,
        [*(org.id for org in slot.orgs), int(item_id)],
        identity=identity,
    )
    manager.dialog_data.pop(FOUND_KEY, None)


@inject
async def remove_org(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
    interactor: FromDishka[SetSlotOrgsInteractor],
    reader: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    slot = await _slot(manager, reader)
    await interactor(
        current_year(manager),
        slot.id,
        [org.id for org in slot.orgs if org.id != int(item_id)],
        identity=identity,
    )


@inject
async def start_compose(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[GetDefaultSlotDatesInteractor],
) -> None:
    # the engine owns the rule even while nothing is persisted
    days = await interactor(current_year(manager))
    manager.dialog_data[COMPOSE_KEY] = [day.isoformat() for day in days]
    await manager.switch_to(states.SeasonSG.compose)


@inject
async def reset_compose(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[GetDefaultSlotDatesInteractor],
) -> None:
    days = await interactor(current_year(manager))
    manager.dialog_data[COMPOSE_KEY] = [day.isoformat() for day in days]


async def toggle_compose_day(
    c: CallbackQuery, widget: Any, manager: DialogManager, day: date
) -> None:
    days = compose_dates(manager)
    if day in days:
        days.remove(day)
    else:
        days.append(day)
    manager.dialog_data[COMPOSE_KEY] = [one.isoformat() for one in sorted(days)]


@inject
async def publish_season(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[PublishSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    year = current_year(manager)
    drafts = [dto.SlotDraft(slot_date=day) for day in compose_dates(manager)]
    await interactor(year, drafts, identity=identity)
    manager.dialog_data.pop(COMPOSE_KEY, None)
    await c.answer("Расписание опубликовано")
    await manager.switch_to(states.SeasonSG.calendar)
