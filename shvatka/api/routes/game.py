import logging
from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Path
from fastapi.responses import StreamingResponse, Response

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import responses, req
from shvatka.api.utils.web_input import WebInput
from shvatka.core.games.interactors import (
    GameFileReaderInteractor,
    GamePlayReaderInteractor,
    GameKeysReaderInteractor,
    GameStatReaderInteractor,
    CheckKeyInteractor,
)
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import enums
from shvatka.core.services.game import (
    get_authors_games,
    get_completed_games,
    get_full_game,
)
from shvatka.infrastructure.db.dao.holder import HolderDao


logger = logging.getLogger(__name__)


@inject
async def get_my_games_list(
    identity: FromDishka[ApiIdentityProvider],
    dao: FromDishka[HolderDao],
):
    return responses.Page(await get_authors_games(identity, dao.game))


@inject
async def get_active_game(
    current_game: FromDishka[CurrentGameProvider],
    response: Response,
) -> responses.Game | None:
    game = await current_game.get_game()
    if game is None:
        raise HTTPException(status_code=404, detail={"text": "game not found"})
    return responses.Game.from_core(game)


@inject
async def get_all_games(
    dao: FromDishka[HolderDao],
) -> responses.Page[responses.Game]:
    games = await get_completed_games(dao.game)
    return responses.Page([responses.Game.from_core(game) for game in games])


@inject
async def get_game_card(
    dao: FromDishka[HolderDao],
    identity: FromDishka[ApiIdentityProvider],
    id_: Annotated[int, Path(alias="id")],
):
    game = await get_full_game(id_, identity, dao.game)
    return responses.FullGame.from_core(game)


@inject
async def get_game_keys(
    interactor: FromDishka[GameKeysReaderInteractor],
    identity: FromDishka[ApiIdentityProvider],
    id_: Annotated[int, Path(alias="id")],
) -> dict[int, list[responses.KeyTime | None]]:
    keys = await interactor(identity=identity, game_id=id_)
    return {k: [responses.KeyTime.from_core(key_time) for key_time in v] for k, v in keys.items()}


@inject
async def get_game_stat(
    interactor: FromDishka[GameStatReaderInteractor],
    identity: FromDishka[ApiIdentityProvider],
    id_: Annotated[int, Path(alias="id")],
) -> responses.GameStat:
    stat = await interactor(identity=identity, game_id=id_)
    return responses.GameStat.from_core(stat)


@inject
async def get_game_file(
    identity: FromDishka[ApiIdentityProvider],
    file_reader: FromDishka[GameFileReaderInteractor],
    id_: Annotated[int, Path(alias="id")],
    guid: Annotated[str, Path(alias="guid")],
) -> StreamingResponse:
    return StreamingResponse(
        (b for b in await file_reader(guid=guid, identity=identity, game_id=id_)),
        headers={
            "Cache-Control": "private, max-age=86400",
            "Vary": "Authorization, Cookie",
        },
    )


@inject
async def get_running_game_hints(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[GamePlayReaderInteractor],
) -> responses.CurrentHintResponse:
    return responses.CurrentHintResponse.from_core(await interactor(identity))


@inject
async def insert_key(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CheckKeyInteractor],
    input_container: FromDishka[WebInput],
    key: Annotated[req.Key, Body()],
) -> responses.InsertedKey:
    await interactor(key=key.text, identity=identity, input_container=input_container)
    if input_container.new_key is None:
        logger.critical("not implemented condition for key %s", key.text)
        raise HTTPException(status_code=500, detail="not implemented state found")
    return responses.InsertedKey(
        text=input_container.new_key.text,
        is_duplicate=input_container.new_key.is_duplicate,
        wrong=input_container.new_key.type_ == enums.KeyType.wrong,
        at=input_container.new_key.at,
        effects=input_container.effects,
        game_finished=input_container.game_finished,
    )


def setup() -> APIRouter:
    router = APIRouter(prefix="/games")
    router.add_api_route("", get_all_games, methods=["GET"])
    router.add_api_route("/my", get_my_games_list, methods=["GET"])
    router.add_api_route("/active", get_active_game, methods=["GET"])
    router.add_api_route("/running/level/current/hints", get_running_game_hints, methods=["GET"])
    router.add_api_route("/running/key", insert_key, methods=["POST"])
    router.add_api_route("/{id}", get_game_card, methods=["GET"])
    router.add_api_route("/{id}/keys", get_game_keys, methods=["GET"])
    router.add_api_route("/{id}/stat", get_game_stat, methods=["GET"])
    router.add_api_route("/{id}/files/{guid}", get_game_file, methods=["GET"])
    return router
