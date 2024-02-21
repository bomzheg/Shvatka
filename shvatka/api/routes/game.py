from typing import BinaryIO, Annotated

from dishka.integrations.base import Depends
from dishka.integrations.fastapi import Depends as DiDepends, inject
from fastapi import APIRouter
from fastapi.params import Path

from shvatka.api.models import responses
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.services.game import get_authors_games, get_completed_games, get_full_game, get_game
from shvatka.core.services.scenario.files import get_file_content
from shvatka.core.utils.exceptions import GameNotFound
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def get_my_games_list(
    player: Annotated[dto.Player, Depends()],
    dao: Annotated[HolderDao, Depends()],
):
    return responses.Page(await get_authors_games(player, dao.game))


@inject
async def get_active_game(
    game: Annotated[dto.Game | None, Depends()],
) -> responses.Game | None:
    return responses.Game.from_core(game)


@inject
async def get_all_games(
    dao: Annotated[HolderDao, Depends()],
) -> responses.Page[responses.Game]:
    games = await get_completed_games(dao.game)
    return responses.Page([responses.Game.from_core(game) for game in games])


@inject
async def get_game_card(
    dao: Annotated[HolderDao, Depends()],
    player: Annotated[dto.Player, Depends()],
    id_: int = Path(alias="id"),  # type: ignore[assignment]
):
    game = await get_full_game(id_, player, dao.game)
    return responses.FullGame.from_core(game)


@inject
async def get_game_file(
    dao: Annotated[HolderDao, Depends()],
    player: Annotated[dto.Player, Depends()],
    file_gateway: Annotated[FileGateway, DiDepends()],
    id_: int = Path(alias="id"),  # type: ignore[assignment]
    guid: str = Path(alias="guid"),  # type: ignore[assignment]
) -> BinaryIO:
    game = await get_game(id_, dao=dao.game)
    return await get_file_content(guid, file_gateway, player, game, dao.file_info)


def setup() -> APIRouter:
    router = APIRouter(prefix="/games")
    router.add_api_route("", get_all_games, methods=["GET"])
    router.add_api_route("/my", get_my_games_list, methods=["GET"])
    router.add_api_route("/active", get_active_game, methods=["GET"])
    router.add_api_route("/{id}", get_game_card, methods=["GET"])
    router.add_api_route("/{id}/files/{guid}", get_game_card, methods=["GET"])
    return router
