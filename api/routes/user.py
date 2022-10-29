import logging
from datetime import datetime

from fastapi import Depends, APIRouter
from pydantic import BaseModel
from starlette.responses import HTMLResponse

from api.dependencies import get_current_user
from shvatka.models import dto

logger = logging.getLogger(__name__)


async def read_own_items(current_user: dto.User = Depends(get_current_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


async def read_users_me(current_user: dto.User = Depends(get_current_user)):
    return current_user


async def login_page():
    return """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <script 
                async src="https://telegram.org/js/telegram-widget.js?21" 
                data-telegram-login="shvatkatestbot" 
                data-size="large" 
                data-auth-url="http://127.0.0.1:8000/login" 
                data-request-access="write"
            ></script>
        </body>
    </html>
    """


class UserTgAuth(BaseModel):
    id: int
    first_name: str
    auth_date: datetime
    hash: str
    username: str | None = None
    last_name: str | None = None


async def login_post(user: UserTgAuth):
    logger.info("user %s", user)


def setup(router: APIRouter):
    router.add_api_route("/users/0", read_users_me, methods=["GET"], response_model=dto.User)
    router.add_api_route("/users/0/items", read_own_items, methods=["GET"])
    router.add_api_route("/login", login_page, response_class=HTMLResponse, methods=["GET"])
    router.add_api_route("/login", login_post, methods=["POST"])
