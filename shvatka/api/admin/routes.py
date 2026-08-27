from io import BytesIO
from typing import Annotated

from adaptix import Retort
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.params import Path, Query

from shvatka.api.app.config.models.main import ApiConfig
from shvatka.api.app.dependencies.auth import ApiIdentityProvider
from shvatka.api.admin import requests, responses
from shvatka.api.shared import requests as shared_requests
from shvatka.api.players import responses as players_responses
from shvatka.api.shared import responses as shared
from shvatka.api.teams import responses as teams_responses
from shvatka.api.games import responses as games_responses
from shvatka.api.files import responses as files_responses
from shvatka.api.waivers import responses as waivers_responses
from shvatka.core.files.interactors import CollectFileGarbageInteractor
from shvatka.core.games.admin_interactors import (
    AdminChangeGameStatusInteractor,
    AdminGamesListInteractor,
    AdminResendCurrentLevelInteractor,
    AdminUpdateGameScenarioInteractor,
    AdminUploadGameFileInteractor,
)
from shvatka.core.models import dto
from shvatka.core.players.admin_interactors import (
    AdminChangePlayerTgInteractor,
    AdminGetPlayerInteractor,
    AdminGetPlayerWaiverPointsInteractor,
    AdminMergePlayersInteractor,
    AdminSearchPlayersInteractor,
    AdminSetPlayerEmailInteractor,
    AdminSetPlayerUsernameInteractor,
)
from shvatka.core.services.one_time_link import GenerateOneTimeLoginLinkForPlayerInteractor
from shvatka.core.services.scenario.files import get_file_metas
from shvatka.core.teams.admin_interactors import (
    AdminAddPlayerToTeamInteractor,
    AdminChangeTeamCaptainInteractor,
    AdminMergeTeamsInteractor,
    AdminRemovePlayerFromTeamInteractor,
)
from shvatka.core.utils import exceptions
from shvatka.core.waiver.admin_interactors import (
    AdminGameWaiversReaderInteractor,
    AdminPollReaderInteractor,
    AdminRemovePollVoteInteractor,
)
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def list_players(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminSearchPlayersInteractor],
    username: Annotated[str | None, Query()] = None,
    name: Annotated[str | None, Query()] = None,
    active: Annotated[bool, Query()] = True,
    archive: Annotated[bool, Query()] = False,
    can_be_author: Annotated[bool | None, Query()] = None,
) -> shared.Items[responses.AdminPlayer]:
    players = await interactor(
        identity,
        username=username,
        name=name,
        active=active,
        archive=archive,
        can_be_author=can_be_author,
    )
    return shared.Items([responses.AdminPlayer.from_core(player) for player in players])


@inject
async def get_player(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminGetPlayerInteractor],
    config: FromDishka[ApiConfig],
    id_: Annotated[int, Path(alias="id")],
) -> players_responses.PlayerWithIdentities:
    info = await interactor(identity, id_)
    return players_responses.PlayerWithIdentities.from_core(
        info.player, info.email, config.superusers
    )


@inject
async def create_one_time_link(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[GenerateOneTimeLoginLinkForPlayerInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.OneTimeLink:
    url = await interactor(identity=identity, player_id=id_)
    return responses.OneTimeLink(url=url)


@inject
async def change_email(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminSetPlayerEmailInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.AdminChangeEmail, Body()],
) -> shared.EmailAccount:
    try:
        account = await interactor(
            identity=identity, player_id=id_, email=body.email, is_verified=body.verified
        )
    except exceptions.EmailAlreadyExist as e:
        raise HTTPException(status_code=409, detail="email already exists") from e
    return shared.EmailAccount(email=account.email, is_verified=account.is_verified)


@inject
async def change_username(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminSetPlayerUsernameInteractor],
    config: FromDishka[ApiConfig],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.AdminChangeUsername, Body()],
) -> players_responses.PlayerWithIdentities:
    try:
        info = await interactor(identity=identity, player_id=id_, username=body.username)
    except exceptions.PlayerInvalidUsername as e:
        raise HTTPException(status_code=422, detail="invalid username") from e
    except exceptions.PlayerUsernameOccupied as e:
        raise HTTPException(status_code=409, detail="username already occupied") from e
    return players_responses.PlayerWithIdentities.from_core(
        info.player, info.email, config.superusers
    )


@inject
async def change_tg(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminChangePlayerTgInteractor],
    config: FromDishka[ApiConfig],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.AdminChangeTg, Body()],
) -> players_responses.PlayerWithIdentities:
    try:
        info = await interactor(
            identity=identity,
            player_id=id_,
            user=dto.User(
                tg_id=body.tg_id,
                username=body.username,
                first_name=body.first_name,
                last_name=body.last_name,
            ),
        )
    except exceptions.PlayerTgAlreadyLinked as e:
        raise HTTPException(
            status_code=409, detail="this telegram account is linked to another player"
        ) from e
    return players_responses.PlayerWithIdentities.from_core(
        info.player, info.email, config.superusers
    )


@inject
async def get_poll(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminPollReaderInteractor],
) -> responses.AdminPoll:
    return responses.AdminPoll.from_core(await interactor(identity))


@inject
async def remove_poll_vote(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminRemovePollVoteInteractor],
    team_id: Annotated[int, Path()],
    player_id: Annotated[int, Path()],
) -> None:
    await interactor(identity=identity, team_id=team_id, player_id=player_id)


@inject
async def get_player_waiver_points(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminGetPlayerWaiverPointsInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> shared.Items[waivers_responses.WaiverPoint]:
    points = await interactor(identity, id_)
    return shared.Items([waivers_responses.WaiverPoint.from_core(point) for point in points])


@inject
async def merge_players(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminMergePlayersInteractor],
    body: Annotated[requests.MergePlayersRequest, Body()],
) -> shared.Player:
    player = await interactor(
        identity=identity,
        primary_id=body.primary_id,
        secondary_id=body.secondary_id,
        timeline=body.core_timeline(),
    )
    return shared.Player.from_core(player)


@inject
async def merge_teams(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminMergeTeamsInteractor],
    body: Annotated[shared_requests.MergeRequest, Body()],
) -> shared.Team:
    team = await interactor(
        identity=identity, primary_id=body.primary_id, secondary_id=body.secondary_id
    )
    result = shared.Team.from_core(team)
    assert result is not None
    return result


@inject
async def change_team_captain(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminChangeTeamCaptainInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.AdminNewCaptain, Body()],
) -> shared.Team:
    team = await interactor(identity=identity, team_id=id_, player_id=body.player_id)
    result = shared.Team.from_core(team)
    assert result is not None
    return result


@inject
async def add_player_to_team(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminAddPlayerToTeamInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.AdminJoinTeam, Body()],
) -> teams_responses.TeamMember:
    team_player = await interactor(
        identity=identity,
        team_id=id_,
        player_id=body.player_id,
        role=body.role,
        emoji=body.emoji,
    )
    return teams_responses.TeamMember.from_core(team_player)


@inject
async def remove_player_from_team(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminRemovePlayerFromTeamInteractor],
    player_id: Annotated[int, Path()],
) -> None:
    await interactor(identity=identity, player_id=player_id)


@inject
async def get_waivers_by_game(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminGameWaiversReaderInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> waivers_responses.WaiversDto:
    return waivers_responses.WaiversDto.from_core(await interactor(identity, id_))


@inject
async def list_games(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminGamesListInteractor],
) -> shared.Page[shared.Game]:
    """Games the admin panel may act on: active and complete ones.

    Their status and nothing else — a game's content is not an admin's to read,
    and a game still being written does not appear here at all.
    """
    games = await interactor(identity)
    return shared.Page([shared.Game.from_core(game) for game in games])


@inject
async def change_game_status(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminChangeGameStatusInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.AdminGameStatusChange, Body()],
) -> shared.Game:
    """Move the game to another status.

    Answers with the game as it now is. Moving it to a status an admin may not
    see (``underconstruction``, ``ready``) is allowed and final: the game is
    its author's again, and this endpoint answers 404 for it afterwards.
    """
    game = await interactor(game_id=id_, status=body.status, identity=identity)
    return shared.Game.from_core(game)


@inject
async def change_game_scenario(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminUpdateGameScenarioInteractor],
    dao: FromDishka[HolderDao],
    retort: FromDishka[Retort],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[requests.AdminGameScenarioEdit, Body()],
) -> games_responses.FullGame:
    game = await interactor(
        game_id=id_,
        raw_scn=body.scenario,
        new_author_id=body.author_id,
        identity=identity,
    )
    files = await get_file_metas(game, identity, dao.game_packager)
    return games_responses.FullGame.from_core(retort, game, files)


@inject
async def resend_current_level(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminResendCurrentLevelInteractor],
    body: Annotated[requests.AdminResendLevel, Body()],
) -> shared.Items[shared.Team]:
    """Send the running level's messages to a team again — telegram lost them.

    With ``team_id`` it goes to that one team, without it to every team of the
    game. The puzzle and the hints the team has already earned go from the
    engine straight to it; the answer names the teams the request covered and
    nothing else — not the level any of them is on, not how many hints it has
    had, not whether it has finished.
    """
    teams = await interactor(identity=identity, team_id=body.team_id)
    rendered = []
    for team in teams:
        one = shared.Team.from_core(team)
        assert one is not None
        rendered.append(one)
    return shared.Items(rendered)


@inject
async def upload_game_file(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminUploadGameFileInteractor],
    id_: Annotated[int, Path(alias="id")],
    file: Annotated[UploadFile, File()],
) -> files_responses.UploadedFile:
    content = BytesIO(await file.read())
    saved = await interactor(
        game_id=id_,
        content=content,
        original_filename=file.filename or "document",
        identity=identity,
    )
    return files_responses.UploadedFile.from_core(saved)


@inject
async def collect_file_garbage(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CollectFileGarbageInteractor],
    dry_run: Annotated[bool, Query()] = True,
) -> responses.FileGarbage:
    """Sweep files nothing refers to any more.

    Defaults to a dry run: the answer says what would go, and only an explicit
    ``dry_run=false`` deletes it.
    """
    return responses.FileGarbage.from_core(await interactor(identity, dry_run=dry_run))


def setup() -> APIRouter:
    router = APIRouter(prefix="/admin", tags=["admin"])
    router.add_api_route("/players", list_players, methods=["GET"])
    router.add_api_route("/players/{id}", get_player, methods=["GET"])
    router.add_api_route("/players/{id}/one-time-link", create_one_time_link, methods=["POST"])
    router.add_api_route("/players/{id}/waiver-points", get_player_waiver_points, methods=["GET"])
    router.add_api_route("/players/{id}/email", change_email, methods=["PUT"])
    router.add_api_route("/players/{id}/username", change_username, methods=["PUT"])
    router.add_api_route("/players/{id}/tg", change_tg, methods=["PUT"])
    router.add_api_route("/poll", get_poll, methods=["GET"])
    router.add_api_route(
        "/poll/{team_id}/players/{player_id}",
        remove_poll_vote,
        methods=["DELETE"],
        status_code=204,
    )
    router.add_api_route("/players/merge", merge_players, methods=["POST"])
    router.add_api_route("/teams/merge", merge_teams, methods=["POST"])
    router.add_api_route("/teams/{id}/captain", change_team_captain, methods=["PUT"])
    router.add_api_route("/teams/{id}/players", add_player_to_team, methods=["POST"])
    router.add_api_route(
        "/teams/{id}/players/{player_id}",
        remove_player_from_team,
        methods=["DELETE"],
        status_code=204,
    )
    router.add_api_route("/waivers/game/{id}", get_waivers_by_game, methods=["GET"])
    router.add_api_route("/games", list_games, methods=["GET"])
    router.add_api_route("/games/{id}/status", change_game_status, methods=["PUT"])
    router.add_api_route("/games/{id}/scenario", change_game_scenario, methods=["PUT"])
    router.add_api_route("/games/{id}/files", upload_game_file, methods=["POST"])
    router.add_api_route("/games/running/resend", resend_current_level, methods=["POST"])
    router.add_api_route("/files/gc", collect_file_garbage, methods=["POST"])
    return router
