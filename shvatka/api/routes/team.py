from fastapi import Depends, APIRouter

from shvatka.api.dependencies import team_provider
from shvatka.api.models import responses
from shvatka.core.models import dto


async def get_my_team(team: dto.Team = Depends(team_provider)) -> responses.Team:
    return responses.Team.from_core(team)


def setup(router: APIRouter):
    router.add_api_route("/teams/my", get_my_team, methods=["GET"])
