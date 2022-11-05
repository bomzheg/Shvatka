from fastapi import Depends, APIRouter

from api.dependencies import team_provider
from shvatka.models import dto


async def get_my_team(team: dto.Team = Depends(team_provider)) -> dto.Team:
    return team


def setup(router: APIRouter):
    router.add_api_route("/teams/my", get_my_team, methods=["GET"])
