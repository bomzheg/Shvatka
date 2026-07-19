from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Path, Query

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import req, responses
from shvatka.api.routes.waivers import WaiversDto
from shvatka.core.models import dto
from shvatka.core.players.admin_interactors import (
    AdminChangePlayerTgInteractor,
    AdminGetPlayerInteractor,
    AdminGetPlayerWaiverPointsInteractor,
    AdminMergePlayersInteractor,
    AdminSearchPlayersInteractor,
    AdminSetPlayerEmailInteractor,
)
from shvatka.core.services.one_time_link import GenerateOneTimeLoginLinkForPlayerInteractor
from shvatka.core.teams.admin_interactors import AdminMergeTeamsInteractor
from shvatka.core.utils import exceptions
from shvatka.core.waiver.admin_interactors import (
    AdminGameWaiversReaderInteractor,
    AdminPollReaderInteractor,
    AdminRemovePollVoteInteractor,
)


@inject
async def list_players(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminSearchPlayersInteractor],
    username: Annotated[str | None, Query()] = None,
    name: Annotated[str | None, Query()] = None,
    active: Annotated[bool, Query()] = True,
    archive: Annotated[bool, Query()] = False,
    can_be_author: Annotated[bool | None, Query()] = None,
) -> responses.Items[responses.AdminPlayer]:
    players = await interactor(
        identity,
        username=username,
        name=name,
        active=active,
        archive=archive,
        can_be_author=can_be_author,
    )
    return responses.Items([responses.AdminPlayer.from_core(player) for player in players])


@inject
async def get_player(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminGetPlayerInteractor],
    config: FromDishka[ApiConfig],
    id_: Annotated[int, Path(alias="id")],
) -> responses.PlayerWithIdentities:
    info = await interactor(identity, id_)
    return responses.PlayerWithIdentities.from_core(info.player, info.email, config.superusers)


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
    body: Annotated[req.AdminChangeEmail, Body()],
) -> responses.EmailAccount:
    try:
        account = await interactor(
            identity=identity, player_id=id_, email=body.email, is_verified=body.verified
        )
    except exceptions.EmailAlreadyExist as e:
        raise HTTPException(status_code=409, detail="email already exists") from e
    return responses.EmailAccount(email=account.email, is_verified=account.is_verified)


@inject
async def change_tg(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminChangePlayerTgInteractor],
    config: FromDishka[ApiConfig],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[req.AdminChangeTg, Body()],
) -> responses.PlayerWithIdentities:
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
    return responses.PlayerWithIdentities.from_core(info.player, info.email, config.superusers)


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
) -> responses.Items[responses.WaiverPoint]:
    points = await interactor(identity, id_)
    return responses.Items([responses.WaiverPoint.from_core(point) for point in points])


@inject
async def merge_players(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminMergePlayersInteractor],
    body: Annotated[req.MergePlayersRequest, Body()],
) -> responses.Player:
    player = await interactor(
        identity=identity,
        primary_id=body.primary_id,
        secondary_id=body.secondary_id,
        timeline=body.core_timeline(),
    )
    return responses.Player.from_core(player)


@inject
async def merge_teams(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminMergeTeamsInteractor],
    body: Annotated[req.MergeRequest, Body()],
) -> responses.Team:
    team = await interactor(
        identity=identity, primary_id=body.primary_id, secondary_id=body.secondary_id
    )
    result = responses.Team.from_core(team)
    assert result is not None
    return result


@inject
async def get_waivers_by_game(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminGameWaiversReaderInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> WaiversDto:
    return WaiversDto.from_core(await interactor(identity, id_))


def setup() -> APIRouter:
    router = APIRouter(prefix="/admin", tags=["admin"])
    router.add_api_route("/players", list_players, methods=["GET"])
    router.add_api_route("/players/{id}", get_player, methods=["GET"])
    router.add_api_route("/players/{id}/one-time-link", create_one_time_link, methods=["POST"])
    router.add_api_route("/players/{id}/waiver-points", get_player_waiver_points, methods=["GET"])
    router.add_api_route("/players/{id}/email", change_email, methods=["PUT"])
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
    router.add_api_route("/waivers/game/{id}", get_waivers_by_game, methods=["GET"])
    return router
