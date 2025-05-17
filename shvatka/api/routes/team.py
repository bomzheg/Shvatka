from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from shvatka.api.models import responses
from shvatka.core.interfaces.identity import IdentityProvider


@inject
async def get_my_team(identity: FromDishka[IdentityProvider]) -> responses.Team | None:
    return responses.Team.from_core(await identity.get_team())


def setup() -> APIRouter:
    router = APIRouter(prefix="/teams")
    router.add_api_route("/my", get_my_team, methods=["GET"])
    return router
