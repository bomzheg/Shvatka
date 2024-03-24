from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi.params import Path
from fastapi.responses import StreamingResponse, Response
from starlette.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from shvatka.api.models import responses
from shvatka.api.utils.error_converter import to_http_error
from shvatka.core.games.interactors import FileReader
from shvatka.core.models import dto
from shvatka.core.services.game import (
    get_authors_games,
    get_completed_games,
    get_full_game,
    get_active,
)
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def get_my_games_list(
    player: Annotated[dto.Player, FromDishka()],
    dao: Annotated[HolderDao, FromDishka()],
):
    return responses.Page(await get_authors_games(player, dao.game))


@inject
async def get_active_game(
    dao: Annotated[HolderDao, FromDishka()],
    response: Response,
) -> responses.Game | None:
    game = await get_active(dao.game)
    if game is None:
        response.status_code = HTTP_404_NOT_FOUND
    return responses.Game.from_core(game)


@inject
async def get_all_games(
    dao: Annotated[HolderDao, FromDishka()],
) -> responses.Page[responses.Game]:
    games = await get_completed_games(dao.game)
    return responses.Page([responses.Game.from_core(game) for game in games])


@inject
async def get_game_card(
    dao: Annotated[HolderDao, FromDishka()],
    player: Annotated[dto.Player, FromDishka()],
    id_: Annotated[int, Path(alias="id")],
):
    game = await get_full_game(id_, player, dao.game)
    return responses.FullGame.from_core(game)


@inject
async def get_game_file(
    user: Annotated[dto.User, FromDishka()],
    file_reader: Annotated[FileReader, FromDishka()],
    id_: Annotated[int, Path(alias="id")],
    guid: Annotated[str, Path(alias="guid")],
) -> StreamingResponse:
    try:
        return StreamingResponse(b for b in await file_reader(guid=guid, user=user, game_id=id_))
    except exceptions.FileNotFound as e:
        raise to_http_error(e, HTTP_404_NOT_FOUND) from e
    except exceptions.NotAuthorizedForEdit as e:
        raise to_http_error(e, HTTP_403_FORBIDDEN) from e


def setup() -> APIRouter:
    router = APIRouter(prefix="/games")
    router.add_api_route("", get_all_games, methods=["GET"])
    router.add_api_route("/my", get_my_games_list, methods=["GET"])
    router.add_api_route("/active", get_active_game, methods=["GET"])
    router.add_api_route("/{id}", get_game_card, methods=["GET"])
    router.add_api_route("/{id}/files/{guid}", get_game_file, methods=["GET"])
    return router
