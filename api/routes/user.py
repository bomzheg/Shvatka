from fastapi import Depends, APIRouter

from api.dependencies import get_current_user
from shvatka.models import dto


async def read_own_items(current_user: dto.User = Depends(get_current_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


async def read_users_me(current_user: dto.User = Depends(get_current_user)):
    return current_user


def setup(router: APIRouter):
    router.add_api_route("/users/0", read_users_me, methods=["GET"], response_model=dto.User)
    router.add_api_route("/users/0/items", read_own_items, methods=["GET"])
