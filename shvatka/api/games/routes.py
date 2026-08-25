import logging
from typing import Annotated, Any

from adaptix import Retort
from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Path
from fastapi.responses import Response

from shvatka.api.app.dependencies.auth import ApiIdentityProvider
from shvatka.api.games import requests, responses
from shvatka.api.games.responses import MyRoleDto
from shvatka.api.shared import responses as shared
from shvatka.api.app.utils.web_input import ApiInput
from shvatka.core.views.game import EffectsKey, GameFinished, KeyShown
from shvatka.core.games.interactors import (
    GamePlayReaderInteractor,
    GameKeysReaderInteractor,
    GameStatReaderInteractor,
    GameResultsFileInteractor,
    CheckKeyInteractor,
    GamePlayRoleReader,
    PassedLevelsReaderInteractor,
)
from shvatka.core.games.editor_interactors import (
    MyGamesInteractor,
    MyGameInteractor,
    CreateGameInteractor,
    ChangeGameScenarioInteractor,
    PlanGameStartInteractor,
    ChangeGameStatusInteractor,
)
from shvatka.core.games.release_interactors import (
    DeleteGameReleaseInteractor,
    GetGameReleaseInteractor,
    SaveGameReleaseInteractor,
)
from shvatka.core.games.org_interactors import (
    ListGameOrgsInteractor,
    AddGameOrgInteractor,
    ChangeOrgPermissionInteractor,
    RemoveGameOrgInteractor,
)
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.scenario.interactors import AllGameKeysPrintInteractor
from shvatka.core.models import enums
from shvatka.core.models.enums.org_permission import OrgPermission
from shvatka.core.services.game import (
    get_completed_games,
    get_full_game,
)
from shvatka.core.services.scenario.files import get_file_metas
from shvatka.infrastructure.db.dao.holder import HolderDao

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MEDIA_TYPE = "application/pdf"


logger = logging.getLogger(__name__)


@inject
async def get_my_games_list(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[MyGamesInteractor],
) -> shared.Page[shared.Game]:
    games = await interactor(identity=identity)
    return shared.Page([shared.Game.from_core(game) for game in games])


@inject
async def get_my_game(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[MyGameInteractor],
    dao: FromDishka[HolderDao],
    retort: FromDishka[Retort],
    id_: Annotated[int, Path(alias="id")],
) -> responses.FullGame:
    game = await interactor(game_id=id_, identity=identity)
    files = await get_file_metas(game, identity, dao.game_packager)
    return responses.FullGame.from_core(retort, game, files)


@inject
async def create_my_game(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CreateGameInteractor],
    game: Annotated[requests.NewGame, Body()],
) -> shared.Game:
    created = await interactor(name=game.name, identity=identity)
    return shared.Game.from_core(created)


@inject
async def change_my_game_scenario(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ChangeGameScenarioInteractor],
    dao: FromDishka[HolderDao],
    retort: FromDishka[Retort],
    id_: Annotated[int, Path(alias="id")],
    scenario: Annotated[dict[str, Any], Body()],
) -> responses.FullGame:
    game = await interactor(game_id=id_, raw_scn=scenario, identity=identity)
    files = await get_file_metas(game, identity, dao.game_packager)
    return responses.FullGame.from_core(retort, game, files)


@inject
async def change_my_game_start_at(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[PlanGameStartInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.GameStartAt, Body()],
) -> shared.Game:
    game = await interactor(game_id=id_, start_at=body.start_at, identity=identity)
    return shared.Game.from_core(game)


@inject
async def change_my_game_status(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ChangeGameStatusInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.GameStatusChange, Body()],
) -> shared.Game:
    game = await interactor(game_id=id_, status=body.status, identity=identity)
    return shared.Game.from_core(game)


@inject
async def get_active_game(
    current_game: FromDishka[CurrentGameProvider],
) -> shared.Game | None:
    game = await current_game.get_game()
    if game is None:
        raise HTTPException(status_code=404, detail={"text": "game not found"})
    return shared.Game.from_core(game)


@inject
async def get_my_role(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[GamePlayRoleReader],
) -> MyRoleDto:
    my_role = await interactor(identity=identity)
    return MyRoleDto.from_core(my_role)


@inject
async def get_all_games(
    dao: FromDishka[HolderDao],
) -> shared.Page[shared.Game]:
    games = await get_completed_games(dao.game)
    return shared.Page([shared.Game.from_core(game) for game in games])


@inject
async def get_game_card(
    dao: FromDishka[HolderDao],
    identity: FromDishka[ApiIdentityProvider],
    retort: FromDishka[Retort],
    id_: Annotated[int, Path(alias="id")],
):
    game = await get_full_game(id_, identity, dao.game)
    files = await get_file_metas(game, identity, dao.game_packager)
    return responses.FullGame.from_core(retort, game, files)


@inject
async def get_game_release(
    interactor: FromDishka[GetGameReleaseInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.GameRelease | None:
    """The game's release, or ``null`` when it has none.

    Readable by anyone — a release is promo, shown to guests too.
    """
    release = await interactor(game_id=id_)
    return None if release is None else responses.GameRelease.from_core(release)


@inject
async def change_my_game_release(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[SaveGameReleaseInteractor],
    retort: FromDishka[Retort],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.GameRelease, Body()],
) -> responses.GameRelease:
    """Write (or rewrite) the release.

    When it reaches the announcements channel is up to the game's status — see
    :mod:`shvatka.core.games.release_interactors`.
    """
    release = await interactor(
        game_id=id_,
        banner=body.banner_to_core(retort),
        hints_=body.hints_to_core(retort),
        identity=identity,
    )
    return responses.GameRelease.from_core(release)


@inject
async def delete_my_game_release(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[DeleteGameReleaseInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> None:
    await interactor(game_id=id_, identity=identity)


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
async def export_game_results(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[GameResultsFileInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> Response:
    file = await interactor(game_id=id_, identity=identity)
    return Response(
        content=file.read(),
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="results_{id_}.xlsx"'},
    )


@inject
async def export_game_keys_to_print(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AllGameKeysPrintInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> Response:
    file = await interactor(id_, identity)
    return Response(
        content=file.read(),
        media_type=PDF_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="keys_{id_}.pdf"'},
    )


@inject
async def get_current_level(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[GamePlayReaderInteractor],
) -> responses.CurrentHintResponse:
    return responses.CurrentHintResponse.from_core(await interactor(identity))


@inject
async def get_passed_levels(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[PassedLevelsReaderInteractor],
) -> responses.PassedLevelsResponse:
    """Hints of the levels the team has already left.

    Separate from the current level on purpose — the client polls the current
    one constantly, and asks for the passed ones only when a player opens them.
    """
    return responses.PassedLevelsResponse.from_core(await interactor(identity))


@inject
async def insert_key(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CheckKeyInteractor],
    input_container: FromDishka[ApiInput],
    current_game: FromDishka[CurrentGameProvider],
    key: Annotated[requests.Key, Body()],
) -> responses.InsertedKey:
    """Answer a key from what the interactor decided to show.

    The same tasks go to telegram in the background; here they are simply read
    rather than sent, so the answer says exactly what the game will say.
    """
    tasks = await interactor(key=key.text, identity=identity, input_container=input_container)
    shown_key = next((task for task in tasks if isinstance(task, KeyShown)), None)
    if shown_key is None:
        logger.critical("not implemented condition for key %s", key.text)
        raise HTTPException(status_code=500, detail="not implemented state found")
    game = await current_game.get_required_full_game()
    level_numbers_by_name_id = {level.name_id: level.number_in_game for level in game.levels}
    return responses.InsertedKey(
        text=shown_key.key.text,
        is_duplicate=shown_key.key.is_duplicate,
        wrong=shown_key.key.type_ == enums.KeyType.wrong,
        at=shown_key.key.at,
        effects=[
            responses.Effects.from_core(task.effects, level_numbers_by_name_id)
            for task in tasks
            if isinstance(task, EffectsKey)
        ],
        game_finished=any(isinstance(task, GameFinished) for task in tasks),
    )


@inject
async def get_game_organizers(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ListGameOrgsInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> shared.Page[responses.GameOrganizer]:
    orgs = await interactor(game_id=id_, identity=identity)
    return shared.Page([responses.GameOrganizer.from_core(org) for org in orgs])


@inject
async def add_game_organizer(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AddGameOrgInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.NewOrg, Body()],
) -> responses.GameOrganizer:
    org = await interactor(game_id=id_, player_id=body.player_id, identity=identity)
    return responses.GameOrganizer.from_core(org)


@inject
async def delete_game_organizer(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[RemoveGameOrgInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.DeleteOrg, Body()],
) -> responses.GameOrganizer:
    org = await interactor(game_id=id_, org_id=body.org_id, identity=identity)
    return responses.GameOrganizer.from_core(org)


@inject
async def change_game_organizer_permission(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ChangeOrgPermissionInteractor],
    id_: Annotated[int, Path(alias="id")],
    org_id: Annotated[int, Path()],
    body: Annotated[requests.OrgPermissionUpdate, Body()],
) -> responses.GameOrganizer:
    try:
        permission = OrgPermission[body.permission]
    except KeyError as e:
        raise HTTPException(
            status_code=422, detail={"text": f"unknown permission {body.permission}"}
        ) from e
    org = await interactor(
        game_id=id_,
        org_id=org_id,
        permission=permission,
        value=body.value,
        identity=identity,
    )
    return responses.GameOrganizer.from_core(org)


def setup() -> APIRouter:
    router = APIRouter()
    games_router = APIRouter(prefix="/games", tags=["games"])
    games_router.add_api_route("", get_all_games, methods=["GET"])
    games_router.add_api_route("/my", get_my_games_list, methods=["GET"])
    games_router.add_api_route("/my", create_my_game, methods=["POST"])
    games_router.add_api_route("/my/{id}", get_my_game, methods=["GET"])
    games_router.add_api_route("/my/{id}/scenario", change_my_game_scenario, methods=["PUT"])
    games_router.add_api_route("/my/{id}/start_at", change_my_game_start_at, methods=["PUT"])
    games_router.add_api_route("/my/{id}/status", change_my_game_status, methods=["PUT"])
    games_router.add_api_route("/my/{id}/keys/print", export_game_keys_to_print, methods=["GET"])
    games_router.add_api_route("/my/{id}/release", change_my_game_release, methods=["PUT"])
    games_router.add_api_route("/my/{id}/release", delete_my_game_release, methods=["DELETE"])
    games_router.add_api_route("/active", get_active_game, methods=["GET"])
    games_router.add_api_route("/active/me", get_my_role, methods=["GET"])
    games_router.add_api_route("/running/level/current", get_current_level, methods=["GET"])
    games_router.add_api_route("/running/level/passed", get_passed_levels, methods=["GET"])
    games_router.add_api_route("/running/key", insert_key, methods=["POST"])
    games_router.add_api_route("/{id}", get_game_card, methods=["GET"])
    games_router.add_api_route("/{id}/release", get_game_release, methods=["GET"])
    games_router.add_api_route("/{id}/keys", get_game_keys, methods=["GET"])
    games_router.add_api_route("/{id}/stat", get_game_stat, methods=["GET"])
    games_router.add_api_route("/{id}/stat/export", export_game_results, methods=["GET"])
    org_router = APIRouter(prefix="/games", tags=["game orgs"])
    org_router.add_api_route("/{id}/organizers", get_game_organizers, methods=["GET"])
    org_router.add_api_route("/{id}/organizers", add_game_organizer, methods=["POST"])
    org_router.add_api_route("/{id}/organizers", delete_game_organizer, methods=["DELETE"])
    org_router.add_api_route(
        "/{id}/organizers/{org_id}", change_game_organizer_permission, methods=["PUT"]
    )
    router.include_router(games_router)
    router.include_router(org_router)
    return router
