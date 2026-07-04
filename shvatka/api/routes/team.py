from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi.params import Body, Path, Query

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import req, responses
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.teams.interactors import (
    AddPlayerToTeamInteractor,
    CreateTeamInteractor,
    EditTeamInteractor,
    GetTeamInteractor,
    RemovePlayerFromTeamInteractor,
    TeamPlayedGamesInteractor,
    TeamPlayersInteractor,
    TeamsListInteractor,
    UpdateTeamPlayerInteractor,
)


@inject
async def get_teams(
    interactor: FromDishka[TeamsListInteractor],
    active: Annotated[bool, Query()] = True,
    archive: Annotated[bool, Query()] = False,
    search: Annotated[str | None, Query()] = None,
) -> responses.Items[responses.TeamWithStat]:
    teams = await interactor(active=active, archive=archive, name=search)
    return responses.Items([responses.TeamWithStat.from_core(team) for team in teams])


@inject
async def get_team_stat(
    interactor: FromDishka[TeamPlayedGamesInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.Items[responses.Game]:
    games = await interactor(id_)
    return responses.Items([responses.Game.from_core(game) for game in games])


@inject
async def get_my_team(identity: FromDishka[IdentityProvider]) -> responses.Team | None:
    return responses.Team.from_core(await identity.get_team())


@inject
async def add_player_to_team(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AddPlayerToTeamInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[req.JoinTeam, Body()],
) -> responses.TeamMember:
    team_player = await interactor(
        team_id=id_,
        player_id=body.player_id,
        identity=identity,
        role=body.role,
        emoji=body.emoji,
    )
    return responses.TeamMember.from_core(team_player)


@inject
async def get_team(
    interactor: FromDishka[GetTeamInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.Team:
    return responses.Team.from_core(await interactor(id_))


@inject
async def create_team(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CreateTeamInteractor],
    body: Annotated[req.NewTeam, Body()],
) -> responses.Team:
    team = await interactor(
        identity=identity,
        name=body.name,
        description=body.description,
    )
    return responses.Team.from_core(team)


@inject
async def edit_team(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[EditTeamInteractor],
    id_: Annotated[int, Path(alias="id")],
    body: Annotated[req.TeamSettings, Body()],
) -> responses.Team:
    team = await interactor(
        team_id=id_,
        identity=identity,
        name=body.name,
        description=body.description,
    )
    return responses.Team.from_core(team)


@inject
async def get_team_players(
    interactor: FromDishka[TeamPlayersInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.Items[responses.TeamMemberWithStat]:
    players = await interactor(id_)
    return responses.Items([responses.TeamMemberWithStat.from_core(player) for player in players])


@inject
async def remove_player_from_team(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[RemovePlayerFromTeamInteractor],
    player_id: Annotated[int, Path()],
) -> None:
    await interactor(player_id=player_id, identity=identity)


@inject
async def update_team_player(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[UpdateTeamPlayerInteractor],
    id_: Annotated[int, Path(alias="id")],
    player_id: Annotated[int, Path()],
    body: Annotated[req.TeamPlayerSettings, Body()],
) -> responses.TeamMember:
    team_player = await interactor(
        team_id=id_,
        player_id=player_id,
        identity=identity,
        role=body.role,
        emoji=body.emoji,
        permissions=body.permissions,
    )
    return responses.TeamMember.from_core(team_player)


def setup() -> APIRouter:
    router = APIRouter(prefix="/teams", tags=["teams"])
    router.add_api_route("", get_teams, methods=["GET"])
    router.add_api_route("", create_team, methods=["POST"], status_code=201)
    router.add_api_route("/my", get_my_team, methods=["GET"])
    router.add_api_route("/{id}/stat", get_team_stat, methods=["GET"])
    router.add_api_route("/{id}", get_team, methods=["GET"])
    router.add_api_route("/{id}", edit_team, methods=["PUT"])
    router.add_api_route("/{id}/players", get_team_players, methods=["GET"])
    router.add_api_route("/{id}/players", add_player_to_team, methods=["POST"])
    router.add_api_route(
        "/{id}/players/{player_id}",
        remove_player_from_team,
        methods=["DELETE"],
        status_code=204,
    )
    router.add_api_route("/{id}/players/{player_id}", update_team_player, methods=["PUT"])
    return router
