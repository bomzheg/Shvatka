from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from shvatka.api.models import responses
from shvatka.core.models import dto


@inject
async def get_my_team(team: FromDishka[dto.Team]) -> responses.Team:
    return responses.Team.from_core(team)


def setup() -> APIRouter:
    router = APIRouter(prefix="/teams")
    router.add_api_route("/my", get_my_team, methods=["GET"])
    return router
