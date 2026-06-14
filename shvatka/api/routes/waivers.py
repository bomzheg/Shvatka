import logging
from dataclasses import dataclass
from typing import Annotated, Iterable

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Path
from sqlalchemy.exc import NoResultFound

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import req, responses
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import dto
from shvatka.core.services.game import get_game
from shvatka.core.waiver.interactors import (
    WaiverCompleteReaderInteractor,
    ReplaceTeamWaiversInteractor,
)
from shvatka.infrastructure.db.dao.holder import HolderDao

logger = logging.getLogger(__name__)


@dataclass
class VotedPlayer:
    player: responses.Player

    @classmethod
    def from_core(cls, voted: dto.VotedPlayer) -> "VotedPlayer":
        return cls(player=responses.Player.from_core(voted.player))


@dataclass(kw_only=True, frozen=True, slots=True)
class WaiversDto:
    teams: list[responses.Team]
    waivers: dict[int, list[VotedPlayer]]

    @classmethod
    def from_core(cls, waiver: dict[dto.Team, Iterable[dto.VotedPlayer]]) -> "WaiversDto":
        return cls(
            teams=[responses.Team.from_core(team) for team in waiver],
            waivers={
                team.id: [VotedPlayer.from_core(w) for w in waivers]
                for team, waivers in waiver.items()
            },
        )


@inject
async def get_current_waivers(
    interactor: FromDishka[WaiverCompleteReaderInteractor],
    current_game: FromDishka[CurrentGameProvider],
) -> WaiversDto | None:
    game = await current_game.get_game()
    if game is None:
        return None
    waivers: dict[dto.Team, Iterable[dto.VotedPlayer]] = await interactor(game)
    return WaiversDto.from_core(waivers)


@inject
async def replace_current_waivers(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ReplaceTeamWaiversInteractor],
    body: Annotated[req.ReplaceWaivers, Body()],
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
) -> WaiversDto:
    try:
        game = await get_game(id_, dao=dao.game)
    except NoResultFound as e:
        logger.info("game %s not found", id_, exc_info=e)
        raise HTTPException(status_code=404, detail={"text": "game not found"}) from e
    waivers: dict[dto.Team, Iterable[dto.VotedPlayer]] = await interactor(game)
    return WaiversDto.from_core(waivers)


def setup() -> APIRouter:
    router = APIRouter(prefix="/waivers")
    router.add_api_route("/game/current", get_current_waivers, methods=["GET"])
    router.add_api_route("/game/current", replace_current_waivers, methods=["PUT"])
    router.add_api_route("/game/{id}", get_waivers_by_game, methods=["GET"])
    return router
