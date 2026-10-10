from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto as core_dto
from shvatka.core.players.interactors import SearchPlayersInteractor
from shvatka.core.season import dto
from shvatka.core.season.interactors import GetSeasonInteractor
from shvatka.core.teams.interactors import MyCaptainedTeamsInteractor
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.tgbot.dialogs.outdated import DialogOutdated
from shvatka.tgbot.views.season import render_season, render_slot, slot_mark

COMPOSE_MARK = "✅"
"""A day of the list being composed. Nothing of it is persisted yet."""

MOVED_MARK = "📆"
"""The date being moved, while the new day is chosen."""

SLOT_GONE = "Эта дата уже удалена из расписания. Окно устарело, открой расписание заново"
NO_SEASON = "Расписание на {year} год ещё не опубликовано"
NOTHING_PLANED = "На {day} в расписании сезона ничего не запланировано"

DAY_FORMAT = r"%d.%m.%Y"


def day_text(day: date | None) -> str:
    return day.strftime(DAY_FORMAT) if day is not None else "?"


YEAR_KEY = "year"
SLOT_DATE_KEY = "slot_date"
SLOT_ID_KEY = "slot_id"
COMPOSE_KEY = "compose"
FOUND_KEY = "found"


def current_year(manager: DialogManager) -> int:
    year = manager.dialog_data.get(YEAR_KEY)
    if year is not None:
        return int(year)
    start_data = manager.start_data if isinstance(manager.start_data, dict) else {}
    return int(start_data.get(YEAR_KEY) or datetime.now(tz=tz_game).year)


def compose_dates(manager: DialogManager) -> list[date]:
    return [date.fromisoformat(day) for day in manager.dialog_data.get(COMPOSE_KEY, [])]


def selected_day(manager: DialogManager) -> date | None:
    raw = manager.dialog_data.get(SLOT_DATE_KEY)
    return date.fromisoformat(raw) if raw else None


async def season_or_none(reader: GetSeasonInteractor, year: int) -> dto.Season | None:
    try:
        return await reader(year)
    except exceptions.SeasonNotFound:
        return None


def sorted_slots(season: dto.Season | None) -> list[dto.Slot]:
    if season is None:
        return []
    return sorted(season.slots, key=lambda slot: (slot.slot_date, slot.id))


def pick_slot(manager: DialogManager, slots: Sequence[dto.Slot]) -> dto.Slot | None:
    """The date the window is about: the chosen one, or the day's first.

    Two short games in one night are two dates on the same day, so a tap can
    land on more than one — the window lists them and remembers which.
    """
    day = selected_day(manager)
    of_day = [slot for slot in slots if slot.slot_date == day]
    slot_id = manager.dialog_data.get(SLOT_ID_KEY)
    chosen = next((slot for slot in of_day if slot.id == slot_id), None)
    return chosen or (of_day[0] if of_day else None)


def require_slot(slot: dto.Slot | None) -> dto.Slot:
    """A window that acts on a date re-checks it is still there.

    A telegram window stays clickable forever, and any author may delete any
    date, so the one this was opened for may be gone by the button press.
    """
    if slot is None:
        raise DialogOutdated(SLOT_GONE, "the slot this window was opened for is gone")
    return slot


def _slot_data(slot: dto.Slot | None, player: core_dto.Player | None) -> dict[str, Any]:
    return {
        "slot_text": render_slot(slot) if slot is not None else None,
        "slot": slot,
        "is_free": slot is not None and slot.is_free,
        "is_taken": slot is not None and not slot.is_free,
        "is_linked": slot is not None and slot.is_linked,
        "can_release": slot is not None and not slot.is_free and not slot.is_linked,
        "orgs": list(slot.orgs) if slot is not None else [],
        "author": slot.author_name if slot is not None else None,
        "mark": slot_mark(slot, player) if slot is not None else None,
    }


@inject
async def get_calendar(
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    reader: FromDishka[GetSeasonInteractor],
    **_,
) -> dict[str, Any]:
    year = current_year(dialog_manager)
    player = await identity.get_player()
    season = await season_or_none(reader, year)
    slots = sorted_slots(season)
    return {
        "year": year,
        "prev_year": year - 1,
        "next_year": year + 1,
        "season": season,
        "slots": slots,
        "marks": {slot.slot_date.isoformat(): slot_mark(slot, player) for slot in slots},
        "season_text": render_season(season) if season else NO_SEASON.format(year=year),
        "has_season": season is not None,
        "can_edit": player is not None and player.can_be_author,
    }


@inject
async def get_slot(
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    reader: FromDishka[GetSeasonInteractor],
    **_,
) -> dict[str, Any]:
    year = current_year(dialog_manager)
    player = await identity.get_player()
    # resolving the date on every render is what keeps the window honest:
    # somebody else may have taken, moved or deleted it since it was opened
    slots = sorted_slots(await season_or_none(reader, year))
    day = selected_day(dialog_manager)
    of_day = [slot for slot in slots if slot.slot_date == day]
    slot = pick_slot(dialog_manager, slots)
    return {
        "year": year,
        "day": day,
        "day_title": day_text(day),
        "nothing_planed": NOTHING_PLANED.format(day=day_text(day)),
        "day_slots": of_day,
        "has_many": len(of_day) > 1,
        "can_edit": player is not None and player.can_be_author,
        # linking takes the date for the game's author, so the owner of a
        # linked date is the one whose game panel the button can open
        "is_my_game": slot is not None and slot.is_linked and slot.is_mine(player),
        **_slot_data(slot, player),
    }


@inject
async def get_take(
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    reader: FromDishka[GetSeasonInteractor],
    teams: FromDishka[MyCaptainedTeamsInteractor],
    **_,
) -> dict[str, Any]:
    year = current_year(dialog_manager)
    player = await identity.get_player()
    slot = require_slot(
        pick_slot(dialog_manager, sorted_slots(await season_or_none(reader, year)))
    )
    # the teams you captain, for an admin too: the panel is where an admin acts as one
    captained = await teams(identity)
    return {
        "year": year,
        "day": slot.slot_date,
        "day_title": day_text(slot.slot_date),
        "teams": [one.team for one in captained],
        "has_teams": bool(captained),
        **_slot_data(slot, player),
    }


@inject
async def get_orgs(
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    reader: FromDishka[GetSeasonInteractor],
    search: FromDishka[SearchPlayersInteractor],
    **_,
) -> dict[str, Any]:
    year = current_year(dialog_manager)
    player = await identity.get_player()
    slot = require_slot(
        pick_slot(dialog_manager, sorted_slots(await season_or_none(reader, year)))
    )
    query = dialog_manager.dialog_data.get(FOUND_KEY)
    named = {org.id for org in slot.orgs}
    # being named on a date is not being an author, so the search is not narrowed
    # by promotion; one word looks at both halves of a name and at the username
    found = (
        [
            one
            for one in await search(username=query.lstrip("@"), name=query)
            if one.id not in named
        ]
        if query
        else []
    )
    return {
        "year": year,
        "day": slot.slot_date,
        "day_title": day_text(slot.slot_date),
        "query": query,
        "found": found,
        "has_found": bool(found),
        **_slot_data(slot, player),
    }


@inject
async def get_move(
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    reader: FromDishka[GetSeasonInteractor],
    **_,
) -> dict[str, Any]:
    year = current_year(dialog_manager)
    player = await identity.get_player()
    slots = sorted_slots(await season_or_none(reader, year))
    slot = require_slot(pick_slot(dialog_manager, slots))
    marks = {one.slot_date.isoformat(): slot_mark(one, player) for one in slots}
    marks[slot.slot_date.isoformat()] = MOVED_MARK
    return {
        "year": year,
        "day": slot.slot_date,
        "day_title": day_text(slot.slot_date),
        "marks": marks,
        **_slot_data(slot, player),
    }


@inject
async def get_compose(dialog_manager: DialogManager, **_) -> dict[str, Any]:
    year = current_year(dialog_manager)
    days = compose_dates(dialog_manager)
    return {
        "year": year,
        "days": days,
        "count": len(days),
        "has_days": bool(days),
        "days_text": "\n".join(day_text(day) for day in days),
        "marks": {day.isoformat(): COMPOSE_MARK for day in days},
    }
