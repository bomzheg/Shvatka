from datetime import datetime
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Body, Query, Response
from starlette import status

from shvatka.api.app.dependencies.auth import ApiIdentityProvider
from shvatka.api.seasons import requests, responses
from shvatka.core.season.interactors import (
    AddSlotInteractor,
    EditSlotNoteInteractor,
    FindSlotsNearGameStartInteractor,
    GetCurrentSeasonInteractor,
    GetDefaultSlotDatesInteractor,
    GetSeasonInteractor,
    LinkGameToSlotInteractor,
    ListSeasonsInteractor,
    MoveSlotInteractor,
    PublishSeasonInteractor,
    ReleaseSlotInteractor,
    RemoveSlotInteractor,
    SetSlotOrgsInteractor,
    TakeSlotInteractor,
    UnlinkGameFromSlotInteractor,
)
from shvatka.core.utils.datetime_utils import tz_game


@inject
async def get_seasons(
    interactor: FromDishka[ListSeasonsInteractor],
) -> responses.SeasonYears:
    return responses.SeasonYears(years=list(await interactor()))


@inject
async def get_current_season(
    interactor: FromDishka[GetCurrentSeasonInteractor],
) -> responses.Season:
    return responses.Season.from_core(await interactor(datetime.now(tz=tz_game)))


@inject
async def get_default_slot_dates(
    interactor: FromDishka[GetDefaultSlotDatesInteractor],
    year: Annotated[int, Query(ge=2000, le=2100)],
) -> responses.DefaultSlotDates:
    return responses.DefaultSlotDates(year=year, dates=await interactor(year))


@inject
async def suggest_slots(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[FindSlotsNearGameStartInteractor],
    at: Annotated[datetime, Query()],
) -> list[responses.Slot]:
    slots = await interactor(at, identity)
    return [responses.Slot.from_core(slot) for slot in slots]


@inject
async def get_season(
    interactor: FromDishka[GetSeasonInteractor],
    year: int,
) -> responses.Season:
    return responses.Season.from_core(await interactor(year))


@inject
async def publish_season(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[PublishSeasonInteractor],
    body: Annotated[requests.PublishSeason, Body()],
) -> responses.Season:
    season = await interactor(
        body.year, [draft.to_core() for draft in body.slots], identity=identity
    )
    return responses.Season.from_core(season)


@inject
async def add_slot(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AddSlotInteractor],
    year: int,
    body: Annotated[requests.AddSlot, Body()],
) -> responses.Slot:
    slot = await interactor(year, body.date, body.note, identity=identity)
    return responses.Slot.from_core(slot)


@inject
async def edit_slot(
    identity: FromDishka[ApiIdentityProvider],
    mover: FromDishka[MoveSlotInteractor],
    note_editor: FromDishka[EditSlotNoteInteractor],
    reader: FromDishka[GetSeasonInteractor],
    year: int,
    slot_id: int,
    body: Annotated[requests.EditSlot, Body()],
) -> responses.Slot:
    slot = None
    if body.date is not None:
        slot = await mover(year, slot_id, body.date, identity=identity)
    if body.note is not None:
        # an omitted note leaves it alone, an empty one clears it
        slot = await note_editor(year, slot_id, body.note or None, identity=identity)
    if slot is None:
        # nothing was asked for: answer with the date as it stands
        season = await reader(year)
        slot = next(one for one in season.slots if one.id == slot_id)
    return responses.Slot.from_core(slot)


@inject
async def remove_slot(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[RemoveSlotInteractor],
    year: int,
    slot_id: int,
) -> Response:
    await interactor(year, slot_id, identity=identity)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@inject
async def take_slot(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[TakeSlotInteractor],
    year: int,
    slot_id: int,
    body: Annotated[requests.TakeSlot, Body()],
) -> responses.Slot:
    slot = await interactor(
        year,
        slot_id,
        author_kind=body.kind(),
        team_id=body.team_id,
        org_player_ids=body.org_player_ids,
        identity=identity,
    )
    return responses.Slot.from_core(slot)


@inject
async def release_slot(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ReleaseSlotInteractor],
    year: int,
    slot_id: int,
) -> responses.Slot:
    return responses.Slot.from_core(await interactor(year, slot_id, identity=identity))


@inject
async def set_slot_orgs(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[SetSlotOrgsInteractor],
    year: int,
    slot_id: int,
    body: Annotated[requests.SetSlotOrgs, Body()],
) -> responses.Slot:
    slot = await interactor(year, slot_id, body.org_player_ids, identity=identity)
    return responses.Slot.from_core(slot)


@inject
async def link_game(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[LinkGameToSlotInteractor],
    year: int,
    slot_id: int,
    body: Annotated[requests.LinkGame, Body()],
) -> responses.Slot:
    slot = await interactor(year, slot_id, body.game_id, identity=identity)
    return responses.Slot.from_core(slot)


@inject
async def unlink_game(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[UnlinkGameFromSlotInteractor],
    year: int,
    slot_id: int,
) -> responses.Slot:
    return responses.Slot.from_core(await interactor(year, slot_id, identity=identity))


def setup() -> APIRouter:
    router = APIRouter(prefix="/seasons", tags=["seasons"])
    # the literal paths are registered before {year}, or they never match
    router.add_api_route("", get_seasons, methods=["GET"])
    router.add_api_route("", publish_season, methods=["POST"])
    router.add_api_route("/current", get_current_season, methods=["GET"])
    router.add_api_route("/defaults", get_default_slot_dates, methods=["GET"])
    router.add_api_route("/slots/suggest", suggest_slots, methods=["GET"])
    router.add_api_route("/{year}", get_season, methods=["GET"])
    router.add_api_route("/{year}/slots", add_slot, methods=["POST"])
    router.add_api_route("/{year}/slots/{slot_id}", edit_slot, methods=["PATCH"])
    router.add_api_route("/{year}/slots/{slot_id}", remove_slot, methods=["DELETE"])
    router.add_api_route("/{year}/slots/{slot_id}/take", take_slot, methods=["POST"])
    router.add_api_route("/{year}/slots/{slot_id}/take", release_slot, methods=["DELETE"])
    router.add_api_route("/{year}/slots/{slot_id}/orgs", set_slot_orgs, methods=["PUT"])
    router.add_api_route("/{year}/slots/{slot_id}/game", link_game, methods=["POST"])
    router.add_api_route("/{year}/slots/{slot_id}/game", unlink_game, methods=["DELETE"])
    return router
