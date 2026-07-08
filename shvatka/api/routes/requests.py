from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Body, Path, Query

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import req, responses
from shvatka.core.notifications.request_interactors import (
    CreateTeamJoinInviteInteractor,
    CreateTeamJoinRequestInteractor,
    CreateOrgInviteInteractor,
    AcceptRequestInteractor,
    DeclineRequestInteractor,
    CancelRequestInteractor,
    ListRequestsInteractor,
)


@inject
async def create_team_join_invite(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CreateTeamJoinInviteInteractor],
    body: Annotated[req.TeamJoinInvite, Body()],
) -> responses.ActionRequest:
    request = await interactor(
        identity=identity,
        team_id=body.team_id,
        player_id=body.player_id,
        role=body.role,
        emoji=body.emoji,
    )
    return responses.ActionRequest.from_core(request)


@inject
async def create_team_join_request(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CreateTeamJoinRequestInteractor],
    body: Annotated[req.TeamJoinRequest, Body()],
) -> responses.ActionRequest:
    request = await interactor(identity=identity, team_id=body.team_id)
    return responses.ActionRequest.from_core(request)


@inject
async def create_org_invite(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CreateOrgInviteInteractor],
    body: Annotated[req.OrgInvite, Body()],
) -> responses.ActionRequest:
    request = await interactor(identity=identity, game_id=body.game_id, player_id=body.player_id)
    return responses.ActionRequest.from_core(request)


@inject
async def accept_request(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[AcceptRequestInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.ActionRequest:
    return responses.ActionRequest.from_core(await interactor(identity=identity, request_id=id_))


@inject
async def decline_request(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[DeclineRequestInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.ActionRequest:
    return responses.ActionRequest.from_core(await interactor(identity=identity, request_id=id_))


@inject
async def cancel_request(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[CancelRequestInteractor],
    id_: Annotated[int, Path(alias="id")],
) -> responses.ActionRequest:
    return responses.ActionRequest.from_core(await interactor(identity=identity, request_id=id_))


@inject
async def get_requests(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[ListRequestsInteractor],
    direction: Annotated[str, Query()] = "incoming",
    pending: Annotated[bool, Query()] = False,
) -> responses.Items[responses.ActionRequest]:
    if direction == "outgoing":
        requests = await interactor.outgoing(identity=identity, only_pending=pending)
    else:
        requests = await interactor.incoming(identity=identity, only_pending=pending)
    return responses.Items([responses.ActionRequest.from_core(r) for r in requests])


def setup() -> APIRouter:
    router = APIRouter(prefix="/requests", tags=["requests"])
    router.add_api_route("", get_requests, methods=["GET"])
    router.add_api_route("/team-join-invite", create_team_join_invite, methods=["POST"])
    router.add_api_route("/team-join", create_team_join_request, methods=["POST"])
    router.add_api_route("/org-invite", create_org_invite, methods=["POST"])
    router.add_api_route("/{id}/accept", accept_request, methods=["POST"])
    router.add_api_route("/{id}/decline", decline_request, methods=["POST"])
    router.add_api_route("/{id}/cancel", cancel_request, methods=["POST"])
    return router
