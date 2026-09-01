from collections.abc import Iterable
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body
from fastapi.params import Path

from shvatka.api.app.dependencies.auth import ApiIdentityProvider
from shvatka.api.waivers import requests, responses
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import dto
from shvatka.core.services.game import get_game
from shvatka.core.waiver.interactors import (
    ReplaceTeamWaiversInteractor,
    WaiverCompleteReaderInteractor,
)
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def get_current_waivers(
    interactor: FromDishka[WaiverCompleteReaderInteractor],
    current_game: FromDishka[CurrentGameProvider],
) -> responses.WaiversDto | None:
    game = await current_game.get_game()
    if game is None:
        return None
    waivers: dict[dto.Team, Iterable[dto.VotedPlayer]] = await interactor(game)
    return responses.WaiversDto.from_core(waivers)


@inject
async def replace_current_waivers(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ReplaceTeamWaiversInteractor],
    body: Annotated[requests.ReplaceWaivers, Body()],
) -> responses.TeamWaivers:
    waivers = await interactor(
        identity=identity,
        votes={vote.player_id: vote.played for vote in body.waivers},
    )
    team = await identity.get_required_team()
    return responses.TeamWaivers.from_core(team, waivers)


@inject
async def get_waivers_by_game(
    interactor: FromDishka[WaiverCompleteReaderInteractor],
    dao: FromDishka[HolderDao],
    id_: Annotated[int, Path(alias="id")],
) -> responses.WaiversDto:
    # a game that is not there raises GameNotFound from the dao, which the
    # error handler already answers with a 404
    game = await get_game(id_, dao=dao.game)
    waivers: dict[dto.Team, Iterable[dto.VotedPlayer]] = await interactor(game)
    return responses.WaiversDto.from_core(waivers)


def setup() -> APIRouter:
    router = APIRouter(prefix="/waivers", tags=["waivers"])
    router.add_api_route("/game/current", get_current_waivers, methods=["GET"])
    router.add_api_route("/game/current", replace_current_waivers, methods=["PUT"])
    router.add_api_route("/game/{id}", get_waivers_by_game, methods=["GET"])
    return router
