from datetime import date, datetime
from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.common.url_factory import UrlFactory
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.season import dto as season_dto
from shvatka.core.season.interactors import (
    GetDefaultSlotDatesInteractor,
    GetSeasonInteractor,
)
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.dialogs.season.calendar import FREE, LINKED, MINE, TAKEN

SLOT_DATE_FORMAT = r"%d.%m"


def current_year() -> int:
    return datetime.now(tz=tz_game).year


def selected_year(manager: DialogManager) -> int:
    year = manager.dialog_data.get("year")
    if isinstance(year, int):
        return year
    start: dict[str, Any] = manager.start_data or {}  # type: ignore[assignment]
    year = start.get("year")
    return year if isinstance(year, int) else current_year()


def draft_dates(manager: DialogManager) -> list[str]:
    """The season being composed. It lives here and nowhere else until published."""
    dates = manager.dialog_data.get("draft")
    return list(dates) if isinstance(dates, list) else []


def mark_of(slot: season_dto.Slot, player: dto.Player | None) -> str:
    if slot.game is not None:
        return LINKED
    if slot.is_free:
        return FREE
    return MINE if slot.is_mine(player) else TAKEN


def marks_of(season: season_dto.Season | None, player: dto.Player | None) -> dict[str, str]:
    if season is None:
        return {}
    return {slot.date.isoformat(): mark_of(slot, player) for slot in season.slots}


def format_day(day: date) -> str:
    return day.strftime(SLOT_DATE_FORMAT)


@inject
async def get_season(
    dialog_manager: DialogManager,
    interactor: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
    **_,
) -> dict[str, Any]:
    year = selected_year(dialog_manager)
    player = await identity.get_player()
    try:
        season: season_dto.Season | None = await interactor(year)
    except exceptions.SeasonNotFound:
        season = None
    return {
        "year": year,
        "season": season,
        "slot_marks": marks_of(season, player),
        "is_missing": season is None,
        "moving": bool(dialog_manager.dialog_data.get("moving")),
        "can_compose": season is None and player is not None and player.can_be_author,
        "is_author": player is not None and player.can_be_author,
    }


async def slot_data(
    dialog_manager: DialogManager,
    interactor: GetSeasonInteractor,
    player: dto.Player | None,
    url_factory: UrlFactory,
) -> dict[str, Any]:
    """What every window about one date needs; shared, not re-fetched per window."""
    year = selected_year(dialog_manager)
    season = await interactor(year)
    slot_id = dialog_manager.dialog_data.get("slot_id")
    slot = next((one for one in season.slots if one.id == slot_id), None)
    picked = dialog_manager.dialog_data.get("picked_date", "")
    is_author = player is not None and player.can_be_author
    return {
        "year": year,
        "slot": slot,
        "picked_date": format_day(date.fromisoformat(picked)) if picked else "",
        "is_author": is_author,
        "is_free": slot is not None and slot.is_free,
        "is_mine": slot is not None and slot.is_mine(player),
        # a free date is any author's to edit; a taken one only its owner's
        "can_edit": is_author and slot is not None and (slot.is_free or slot.is_mine(player)),
        "author_name": slot.author_name if slot is not None else None,
        "orgs": list(slot.orgs) if slot is not None else [],
        "game_url": (
            url_factory.get_game_id_web_url(slot.game.id)
            if slot is not None and slot.game is not None
            else ""
        ),
    }


@inject
async def get_slot(
    dialog_manager: DialogManager,
    interactor: FromDishka[GetSeasonInteractor],
    identity: FromDishka[IdentityProvider],
    url_factory: FromDishka[UrlFactory],
    **_,
) -> dict[str, Any]:
    return await slot_data(dialog_manager, interactor, await identity.get_player(), url_factory)


@inject
async def get_take(
    dialog_manager: DialogManager,
    interactor: FromDishka[GetSeasonInteractor],
    dao: FromDishka[HolderDao],
    identity: FromDishka[IdentityProvider],
    url_factory: FromDishka[UrlFactory],
    **_,
) -> dict[str, Any]:
    player = await identity.get_required_player()
    data = await slot_data(dialog_manager, interactor, player, url_factory)
    teams = await dao.team.get_captained_teams(player)
    kind = dialog_manager.dialog_data.get("author_kind", season_dto.SlotAuthorKind.player.name)
    return {
        **data,
        "teams": teams,
        "has_teams": bool(teams),
        "as_team": kind == season_dto.SlotAuthorKind.team.name,
        "team_id": dialog_manager.dialog_data.get("team_id"),
    }


@inject
async def get_orgs(
    dialog_manager: DialogManager,
    dao: FromDishka[HolderDao],
    **_,
) -> dict[str, Any]:
    org_ids = dialog_manager.dialog_data.get("org_ids") or []
    orgs = [await dao.player.get_by_id(int(id_)) for id_ in org_ids]
    return {
        "year": selected_year(dialog_manager),
        "orgs": orgs,
        "has_orgs": bool(orgs),
    }


@inject
async def get_compose(
    dialog_manager: DialogManager,
    interactor: FromDishka[GetDefaultSlotDatesInteractor],
    **_,
) -> dict[str, Any]:
    year = selected_year(dialog_manager)
    dates = draft_dates(dialog_manager)
    if not dates:
        dates = [day.isoformat() for day in await interactor(year)]
        dialog_manager.dialog_data["draft"] = dates
    return {
        "year": year,
        "slot_marks": dict.fromkeys(dates, FREE),
        "dates": [format_day(date.fromisoformat(one)) for one in sorted(dates)],
        "dates_count": len(dates),
        "has_dates": bool(dates),
    }
