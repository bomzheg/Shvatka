from typing import Annotated

from dishka.integrations.base import Depends
from dishka.integrations.fastapi import inject
from fastapi import Depends as fDepends
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import HTMLResponse, Response

from shvatka.api.config.models.auth import AuthConfig
from shvatka.api.models.auth import UserTgAuth, Token
from shvatka.core.services.user import upsert_user
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties, check_tg_hash

TG_WIDGET_HTML = """
        <html>
            <head>
                <title>Authenticate by TG</title>
            </head>
            <body>
                <script
                    async src="https://telegram.org/js/telegram-widget.js?21"
                    data-telegram-login="{bot_username}"
                    data-size="large"
                    data-auth-url="{auth_url}"
                    data-request-access="write"
                ></script>
            </body>
        </html>
        """


@inject
async def login(
    response: Response,
    auth_properties: Annotated[AuthProperties, Depends()],
    config: Annotated[AuthConfig, Depends()],
    dao: Annotated[HolderDao, Depends()],
    form_data: OAuth2PasswordRequestForm = fDepends(),
):
    user = await auth_properties.authenticate_user(form_data.username, form_data.password, dao)
    token = auth_properties.create_user_token(user)
    response.set_cookie(
        "Authorization",
        value=f"{token.token_type} {token.access_token}",
        samesite=config.samesite,
        domain=config.domain,
        httponly=config.httponly,
        secure=config.secure,
    )
    return {"ok": True}


@inject
async def tg_login_result(
    user: Annotated[UserTgAuth, fDepends()],
    dao: Annotated[HolderDao, Depends()],
    auth_properties: Annotated[AuthProperties, Depends()],
    config: Annotated[AuthConfig, Depends()],
) -> Token:
    check_tg_hash(user, config.bot_token)
    await upsert_user(user.to_dto(), dao.user)
    return auth_properties.create_user_token(user.to_dto())


@inject
async def tg_login_page(config: Annotated[AuthConfig, Depends()]):
    return TG_WIDGET_HTML.format(
        bot_username=config.bot_username,
        auth_url=config.auth_url,
    )


def setup() -> APIRouter:
    router = APIRouter(prefix="/auth")
    router.add_api_route("/token", login, methods=["POST"])
    router.add_api_route("/login", tg_login_page, response_class=HTMLResponse, methods=["GET"])
    router.add_api_route("/login/data", tg_login_result, methods=["GET"])
    return router
