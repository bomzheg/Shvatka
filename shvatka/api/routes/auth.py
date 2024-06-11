import typing
from typing import Annotated

from aiogram.types import User
from dishka.integrations.fastapi import inject, FromDishka
from fastapi import Depends as fDepends, Body
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import HTMLResponse, Response

from shvatka.api.config.models.auth import AuthConfig
from shvatka.api.models.auth import UserTgAuth, WebAppAuth
from shvatka.api.utils.cookie_auth import set_auth_response
from shvatka.core.models import dto
from shvatka.core.services.user import upsert_user
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.api.dependencies.auth import AuthProperties, check_tg_hash, check_webapp_hash

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
    auth_properties: FromDishka[AuthProperties],
    config: FromDishka[AuthConfig],
    dao: FromDishka[HolderDao],
    form_data: OAuth2PasswordRequestForm = fDepends(),
):
    user = await auth_properties.authenticate_user(form_data.username, form_data.password, dao)
    token = auth_properties.create_user_token(user)
    set_auth_response(config, response, token)
    return {"ok": True}


@inject
async def logout(
    response: Response,
    config: FromDishka[AuthConfig],
):
    response.delete_cookie(
        "Authorization",
        samesite=config.samesite,
        domain=config.domain,
        httponly=config.httponly,
        secure=config.secure,
    )
    return {"ok": True}


@inject
async def tg_login_result(
    response: Response,
    user: Annotated[UserTgAuth, fDepends()],
    dao: FromDishka[HolderDao],
    auth_properties: FromDishka[AuthProperties],
    config: FromDishka[AuthConfig],
):
    check_tg_hash(user, config.bot_token)
    saved = await upsert_user(user.to_dto(), dao.user)
    token = auth_properties.create_user_token(saved)
    set_auth_response(config, response, token)
    return {"ok": True}


@inject
async def tg_login_result_post(
    response: Response,
    user: Annotated[UserTgAuth, Body()],
    dao: FromDishka[HolderDao],
    auth_properties: FromDishka[AuthProperties],
    config: FromDishka[AuthConfig],
):
    check_tg_hash(user, config.bot_token)
    saved = await upsert_user(user.to_dto(), dao.user)
    token = auth_properties.create_user_token(saved)
    set_auth_response(config, response, token)
    return {"ok": True}


@inject
async def webapp_login_result_post(
    response: Response,
    web_auth: Annotated[WebAppAuth, Body()],
    dao: FromDishka[HolderDao],
    auth_properties: FromDishka[AuthProperties],
    config: FromDishka[AuthConfig],
):
    parsed = check_webapp_hash(web_auth.init_data, config.bot_token)
    user = dto.User.from_aiogram(typing.cast(User, parsed.user))
    saved = await upsert_user(user, dao.user)
    token = auth_properties.create_user_token(saved)
    set_auth_response(config, response, token)
    return {"ok": True}


@inject
async def tg_login_page(config: FromDishka[AuthConfig]):
    return TG_WIDGET_HTML.format(
        bot_username=config.bot_username,
        auth_url=config.auth_url,
    )


def setup() -> APIRouter:
    router = APIRouter(prefix="/auth")
    router.add_api_route("/token", login, methods=["POST"])
    router.add_api_route("/login", tg_login_page, response_class=HTMLResponse, methods=["GET"])
    router.add_api_route("/logout", logout, methods=["POST"])
    router.add_api_route("/login/data", tg_login_result, methods=["GET"])
    router.add_api_route("/login/data", tg_login_result_post, methods=["POST"])
    router.add_api_route("/login/webapp", webapp_login_result_post, methods=["POST"])
    return router
