import logging
from typing import Annotated, Iterable

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, HTTPException
from fastapi.params import Path, Query
from sqlalchemy.exc import NoResultFound

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.dependencies.admin import Superuser
from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import req, responses
from shvatka.api.routes.waivers import WaiversDto
from shvatka.core.models import dto
from shvatka.core.players.admin_interactors import (
    AdminChangePlayerTgInteractor,
    AdminMergePlayersInteractor,
    AdminSetPlayerEmailInteractor,
)
from shvatka.core.players.interactors import GetPlayerInteractor, SearchPlayersInteractor
from shvatka.core.services.one_time_link import GenerateOneTimeLoginLinkForPlayerInteractor
from shvatka.core.teams.admin_interactors import AdminMergeTeamsInteractor
from shvatka.core.utils import exceptions
from shvatka.core.waiver.admin_interactors import (
    AdminPollReaderInteractor,
    AdminRemovePollVoteInteractor,
)
from shvatka.core.waiver.interactors import WaiverCompleteReaderInteractor
from shvatka.core.services.game import get_game
from shvatka.infrastructure.db.dao.holder import HolderDao

logger = logging.getLogger(__name__)


@inject
async def list_players(
    _superuser: FromDishka[Superuser],
    interactor: FromDishka[SearchPlayersInteractor],
    username: Annotated[str | None, Query()] = None,
    name: Annotated[str | None, Query()] = None,
    active: Annotated[bool, Query()] = True,
    archive: Annotated[bool, Query()] = False,
    can_be_author: Annotated[bool | None, Query()] = None,
) -> responses.Items[responses.AdminPlayer]:
    players = await interactor(
        username=username,
        name=name,
        active=active,
        archive=archive,
        can_be_author=can_be_author,
    )
    return responses.Items([responses.AdminPlayer.from_core(player) for player in players])


@inject
async def get_player(
    _superuser: FromDishka[Superuser],
    interactor: FromDishka[GetPlayerInteractor],
    dao: FromDishka[HolderDao],
    config: FromDishka[ApiConfig],
    id_: Annotated[int, Path(alias="id")],
) -> responses.PlayerWithIdentities:
    info = await interactor(id_)
    email = await dao.email.get_by_player_id(info.player.id)
    return responses.PlayerWithIdentities.from_core(info.player, email, config.superusers)


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
    dao: FromDishka[HolderDao],
    config: FromDishka[ApiConfig],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[req.AdminChangeTg, Body()],
) -> responses.PlayerWithIdentities:
    try:
        player = await interactor(
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
    email = await dao.email.get_by_player_id(player.id)
    return responses.PlayerWithIdentities.from_core(player, email, config.superusers)


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
async def merge_players(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminMergePlayersInteractor],
    body: Annotated[req.MergeRequest, Body()],
) -> responses.Player:
    try:
        player = await interactor(
            identity=identity, primary_id=body.primary_id, secondary_id=body.secondary_id
        )
    except NoResultFound as e:
        logger.info("player not found while merging", exc_info=e)
        raise HTTPException(status_code=404, detail={"text": "player not found"}) from e
    return responses.Player.from_core(player)


@inject
async def merge_teams(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AdminMergeTeamsInteractor],
    body: Annotated[req.MergeRequest, Body()],
) -> responses.Team:
    try:
        team = await interactor(
            identity=identity, primary_id=body.primary_id, secondary_id=body.secondary_id
        )
    except NoResultFound as e:
        logger.info("team not found while merging", exc_info=e)
        raise HTTPException(status_code=404, detail={"text": "team not found"}) from e
    result = responses.Team.from_core(team)
    assert result is not None
    return result


@inject
async def get_waivers_by_game(
    _superuser: FromDishka[Superuser],
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
    router = APIRouter(prefix="/admin", tags=["admin"])
    router.add_api_route("/players", list_players, methods=["GET"])
    router.add_api_route("/players/{id}", get_player, methods=["GET"])
    router.add_api_route("/players/{id}/one-time-link", create_one_time_link, methods=["POST"])
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
