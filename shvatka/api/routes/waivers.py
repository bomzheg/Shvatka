import logging
from dataclasses import dataclass
from typing import Iterable

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from shvatka.api.models import responses
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import dto
from shvatka.core.waiver.interactors import WaiverCompleteReaderInteractor

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
async def get_waivers(
    interactor: FromDishka[WaiverCompleteReaderInteractor],
    current_game: FromDishka[CurrentGameProvider],
) -> WaiversDto | None:
    game = await current_game.get_game()
    if game is None:
        return None
    waivers: dict[dto.Team, Iterable[dto.VotedPlayer]] = await interactor(game)
    return WaiversDto.from_core(waivers)


def setup() -> APIRouter:
    router = APIRouter(prefix="/waivers")
    router.add_api_route("/game/current", get_waivers, methods=["GET"])
    return router
