import logging
from datetime import date, datetime, timedelta
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import AsyncContainer, FromDishka
from dishka.integrations.aiogram import CONTAINER_NAME
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.season import dto as season_dto
from shvatka.core.season.interactors import (
    AddSlotInteractor,
    FindSlotsNearGameStartInteractor,
    GetSeasonInteractor,
    LinkGameToSlotInteractor,
    MoveSlotInteractor,
    PublishSeasonInteractor,
    ReleaseSlotInteractor,
    RemoveSlotInteractor,
    SetSlotOrgsInteractor,
    TakeSlotInteractor,
    UnlinkGameFromSlotInteractor,
)
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.dialogs.season.getters import (
    current_year,
    draft_dates,
    format_day,
    selected_year,
)

logger = logging.getLogger(__name__)

NEAREST_SLOT_WINDOW = timedelta(days=21)
"""How far the "nothing nearby" warning looks for a date worth moving."""


# ---------- the calendar ----------


async def shift_year(manager: DialogManager, by: int) -> None:
    manager.dialog_data["year"] = selected_year(manager) + by
    manager.dialog_data.pop("draft", None)


async def prev_year(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    await shift_year(manager, -1)


async def cancel_move(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    manager.dialog_data["moving"] = False
    await manager.switch_to(states.SeasonSG.slot)


async def next_year(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    await shift_year(manager, 1)


@inject
async def pick_date(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    selected_date: date,
    interactor: FromDishka[GetSeasonInteractor],
    mover: FromDishka[MoveSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    """Open the date that was tapped — or, while moving one, move it here."""
    year = selected_year(manager)
    if manager.dialog_data.get("moving"):
        await mover(year, _slot_id(manager), selected_date, identity=identity)
        manager.dialog_data["moving"] = False
        manager.dialog_data["picked_date"] = selected_date.isoformat()
        await c.answer("Дата перенесена")
        await manager.switch_to(states.SeasonSG.slot)
        return
    season = await interactor(year)
    slot = next((one for one in season.slots if one.date == selected_date), None)
    manager.dialog_data["picked_date"] = selected_date.isoformat()
    manager.dialog_data["slot_id"] = slot.id if slot is not None else None
    await manager.switch_to(states.SeasonSG.slot)


async def start_move(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    """A move is picked on the calendar itself — there is nowhere better to pick a day."""
    manager.dialog_data["moving"] = True
    await manager.switch_to(states.SeasonSG.calendar)


@inject
async def add_slot(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[AddSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    picked = manager.dialog_data["picked_date"]
    slot = await interactor(
        selected_year(manager), date.fromisoformat(picked), None, identity=identity
    )
    manager.dialog_data["slot_id"] = slot.id
    await c.answer("Дата добавлена")


# ---------- one date ----------


def _slot_id(manager: DialogManager) -> int:
    slot_id = manager.dialog_data.get("slot_id")
    if not isinstance(slot_id, int):
        raise exceptions.SlotNotFound(text="no date is selected any more")
    return slot_id


async def to_take(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    manager.dialog_data["author_kind"] = season_dto.SlotAuthorKind.player.name
    manager.dialog_data["team_id"] = None
    manager.dialog_data["org_ids"] = []
    await manager.switch_to(states.SeasonSG.take)


async def as_player(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    manager.dialog_data["author_kind"] = season_dto.SlotAuthorKind.player.name
    manager.dialog_data["team_id"] = None


async def as_team(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    manager.dialog_data["author_kind"] = season_dto.SlotAuthorKind.team.name
    manager.dialog_data["team_id"] = int(item_id)


@inject
async def take_slot(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[TakeSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    kind = season_dto.SlotAuthorKind[
        manager.dialog_data.get("author_kind", season_dto.SlotAuthorKind.player.name)
    ]
    await interactor(
        selected_year(manager),
        _slot_id(manager),
        author_kind=kind,
        team_id=manager.dialog_data.get("team_id"),
        org_player_ids=[int(one) for one in manager.dialog_data.get("org_ids") or []],
        identity=identity,
    )
    await c.answer("Дата за вами")
    await manager.switch_to(states.SeasonSG.slot)


@inject
async def release_slot(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[ReleaseSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    await interactor(selected_year(manager), _slot_id(manager), identity=identity)
    await c.answer("Дата свободна")


@inject
async def remove_slot(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[RemoveSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    await interactor(selected_year(manager), _slot_id(manager), identity=identity)
    manager.dialog_data["slot_id"] = None
    await c.answer("Дата удалена")
    await manager.switch_to(states.SeasonSG.calendar)


@inject
async def unlink_game(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[UnlinkGameFromSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    await interactor(selected_year(manager), _slot_id(manager), identity=identity)
    await c.answer("Игра отвязана")


# ---------- the orgs of a date ----------


async def to_orgs(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    await manager.switch_to(states.SeasonSG.orgs)


@inject
async def add_org(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    dao: FromDishka[HolderDao],
) -> None:
    """Being named on a date is not being an author: any player will do."""
    assert m.text
    player = await dao.player.get_by_username_or_none(m.text.strip().removeprefix("@"))
    if player is None:
        await m.answer("Не удалось найти игрока по этому username")
        return
    org_ids = [int(one) for one in manager.dialog_data.get("org_ids") or []]
    if player.id not in org_ids:
        org_ids.append(player.id)
    manager.dialog_data["org_ids"] = org_ids
    await m.answer(f"{player.name_mention} будет оргом на эту дату")


async def clear_orgs(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    manager.dialog_data["org_ids"] = []
    await c.answer("Список оргов очищен")


@inject
async def save_orgs(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[SetSlotOrgsInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    await interactor(
        selected_year(manager),
        _slot_id(manager),
        [int(one) for one in manager.dialog_data.get("org_ids") or []],
        identity=identity,
    )
    await c.answer("Орги сохранены")
    await manager.switch_to(states.SeasonSG.slot)


# ---------- composing ----------


async def start_compose(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    await manager.switch_to(states.SeasonSG.compose)


async def toggle_draft_date(
    c: CallbackQuery, widget: Any, manager: DialogManager, selected_date: date
) -> None:
    """Nothing is persisted: the list being composed lives in `dialog_data`."""
    dates = draft_dates(manager)
    iso = selected_date.isoformat()
    if iso in dates:
        dates.remove(iso)
    else:
        dates.append(iso)
    manager.dialog_data["draft"] = sorted(dates)


async def to_confirm_publish(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    if not draft_dates(manager):
        await c.answer("В расписании должна быть хотя бы одна дата")
        return
    await manager.switch_to(states.SeasonSG.confirm_publish)


@inject
async def publish_season(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    interactor: FromDishka[PublishSeasonInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    year = selected_year(manager)
    drafts = [season_dto.SlotDraft(date=date.fromisoformat(one)) for one in draft_dates(manager)]
    await interactor(year, drafts, identity=identity)
    manager.dialog_data.pop("draft", None)
    await c.answer("Расписание опубликовано")
    await manager.switch_to(states.SeasonSG.calendar)


async def cancel_compose(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    manager.dialog_data.pop("draft", None)
    await manager.switch_to(states.SeasonSG.calendar)


# ---------- the link offer, grafted onto GameScheduleSG ----------


async def offer_slots(manager: DialogManager, at: datetime) -> None:
    """Fill the offer window's data. Never raises: no schedule is not an error.

    Called from another dialog's handler rather than by aiogram_dialog, so the
    container comes from the manager instead of a `@inject` decorator.
    """
    dishka: AsyncContainer = manager.middleware_data[CONTAINER_NAME]
    interactor = await dishka.get(FindSlotsNearGameStartInteractor)
    identity = await dishka.get(IdentityProvider)
    try:
        candidates = await interactor(at, identity)
        nearest = candidates or await interactor(at, identity, NEAREST_SLOT_WINDOW)
    except Exception as e:  # noqa: BLE001
        logger.warning("can't look for dates near %s", at, exc_info=e)
        candidates, nearest = [], []
    manager.dialog_data["candidates"] = [
        {"id": slot.id, "date": slot.date.isoformat(), "label": format_day(slot.date)}
        for slot in candidates
    ]
    manager.dialog_data["nearest"] = (
        {
            "id": nearest[0].id,
            "date": nearest[0].date.isoformat(),
            "label": format_day(nearest[0].date),
        }
        if nearest
        else None
    )
    manager.dialog_data["game_date"] = at.astimezone(tz_game).date().isoformat()


@inject
async def link_to_slot(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
    interactor: FromDishka[LinkGameToSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    game_id = _game_id(manager)
    day = date.fromisoformat(manager.dialog_data["game_date"])
    await interactor(day.year, int(item_id), game_id, identity=identity)
    await c.answer("Игра привязана к дате")
    await manager.done()


@inject
async def add_and_link(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    adder: FromDishka[AddSlotInteractor],
    linker: FromDishka[LinkGameToSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    day = date.fromisoformat(manager.dialog_data["game_date"])
    slot = await adder(day.year, day, None, identity=identity)
    await linker(day.year, slot.id, _game_id(manager), identity=identity)
    await c.answer("Дата добавлена и привязана")
    await manager.done()


@inject
async def move_nearest_and_link(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    linker: FromDishka[LinkGameToSlotInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    nearest = manager.dialog_data.get("nearest")
    if not nearest:
        await c.answer("Поблизости нет даты, которую можно перенести")
        return
    day = date.fromisoformat(manager.dialog_data["game_date"])
    # linking moves the date onto the game's start, which is the move itself
    await linker(day.year, int(nearest["id"]), _game_id(manager), identity=identity)
    await c.answer("Ближайшая дата перенесена и привязана")
    await manager.done()


async def skip_schedule(c: CallbackQuery, widget: Button, manager: DialogManager) -> None:
    await manager.done()


def _game_id(manager: DialogManager) -> int:
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    return int(data["my_game_id"])


def default_year() -> int:
    return current_year()
