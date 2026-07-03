import contextlib
import typing
from typing import Annotated

from aiogram.types import User
from dishka.integrations.fastapi import inject, FromDishka
from fastapi import Depends as fDepends, Body
from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import HTMLResponse, Response

from shvatka.api.config.models.auth import AuthConfig
from shvatka.api.models.auth import (
    UserTgAuth,
    WebAppAuth,
    OneTimeToken,
    EmailRegister,
    EmailLogin,
    EmailConfirm,
    EmailResend,
    EmailLink,
    ForgotPassword,
)
from shvatka.api.utils.cookie_auth import set_auth_response
from shvatka.core.interfaces.bus import Bus, OneTimeTokenUsed
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.players.player import upsert_player
from shvatka.core.services.email import (
    EmailRegisterInteractor,
    EmailLinkInteractor,
    EmailConfirmInteractor,
    EmailResendInteractor,
    ForgotPasswordInteractor,
)
from shvatka.core.services.user import upsert_user
from shvatka.core.utils import exceptions
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
    player = await upsert_player(saved, dao.player)
    token = auth_properties.create_user_token(player)
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
    player = await upsert_player(saved, dao.player)
    token = auth_properties.create_user_token(player)
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
    player = await upsert_player(saved, dao.player)
    token = auth_properties.create_user_token(player)
    set_auth_response(config, response, token)
    return {"ok": True}


@inject
async def tg_login_page(config: FromDishka[AuthConfig]):
    return TG_WIDGET_HTML.format(
        bot_username=config.bot_username,
        auth_url=config.auth_url,
    )


@inject
async def one_time_token_login(
    one_time_token: Annotated[OneTimeToken, Body()],
    holder: FromDishka[HolderDao],
    auth_properties: FromDishka[AuthProperties],
    config: FromDishka[AuthConfig],
    bus: FromDishka[Bus],
    response: Response,
):
    player_data = await holder.one_time_token.get_invite(token=one_time_token.token)
    if not player_data or (player_id := player_data.get("player_id", None)) is None:
        raise exceptions.SaltError
    token = auth_properties.create_user_id_token(player_id)
    set_auth_response(config, response, token)
    await bus.submit(OneTimeTokenUsed(player_id=player_id))
    return {"ok": True}


@inject
async def email_register(
    body: Annotated[EmailRegister, Body()],
    interactor: FromDishka[EmailRegisterInteractor],
):
    try:
        await interactor(username=body.username, email=body.email, password=body.password)
    except exceptions.EmailInvalid as e:
        raise HTTPException(status_code=422, detail="invalid email") from e
    except exceptions.PlayerInvalidUsername as e:
        raise HTTPException(status_code=422, detail="invalid username") from e
    except exceptions.EmailAlreadyExist as e:
        raise HTTPException(status_code=409, detail="email already exists") from e
    except exceptions.PlayerUsernameOccupied as e:
        raise HTTPException(status_code=409, detail="username already occupied") from e
    return {"ok": True}


@inject
async def email_login(
    response: Response,
    body: Annotated[EmailLogin, Body()],
    dao: FromDishka[HolderDao],
    auth_properties: FromDishka[AuthProperties],
    config: FromDishka[AuthConfig],
):
    player = await auth_properties.authenticate_by_email(body.email, body.password, dao)
    token = auth_properties.create_user_token(player)
    set_auth_response(config, response, token)
    return {"ok": True}


@inject
async def email_confirm(
    body: Annotated[EmailConfirm, Body()],
    interactor: FromDishka[EmailConfirmInteractor],
):
    try:
        await interactor(email=body.email, code=body.code)
    except exceptions.EmailConfirmationCodeInvalid as e:
        raise HTTPException(status_code=400, detail="invalid or expired code") from e
    return {"ok": True}


@inject
async def email_resend(
    body: Annotated[EmailResend, Body()],
    interactor: FromDishka[EmailResendInteractor],
):
    # do not disclose whether the email is registered
    with contextlib.suppress(exceptions.EmailNotFound):
        await interactor(email=body.email)
    return {"ok": True}


@inject
async def email_link(
    body: Annotated[EmailLink, Body()],
    identity: FromDishka[IdentityProvider],
    interactor: FromDishka[EmailLinkInteractor],
):
    player = await identity.get_required_player()
    try:
        await interactor(player=player, email=body.email)
    except exceptions.EmailInvalid as e:
        raise HTTPException(status_code=422, detail="invalid email") from e
    except exceptions.EmailAlreadyExist as e:
        raise HTTPException(status_code=409, detail="email already exists") from e
    return {"ok": True}


@inject
async def forgot_password(
    body: Annotated[ForgotPassword, Body()],
    interactor: FromDishka[ForgotPasswordInteractor],
):
    try:
        await interactor(email=body.email)
    except exceptions.RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail="too many requests") from e
    # do not disclose whether the email is registered
    return {"ok": True}


@inject
async def link_tg(
    user: Annotated[UserTgAuth, Body()],
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
    config: FromDishka[AuthConfig],
):
    check_tg_hash(user, config.bot_token)
    player = await identity.get_required_player()
    if player.has_user():
        raise HTTPException(status_code=409, detail="player already has linked telegram")
    saved = await upsert_user(user.to_dto(), dao.user)
    try:
        existing = await dao.player.get_by_user_id(saved.tg_id)
    except exceptions.PlayerNotFoundError:
        existing = None
    if existing is not None and existing.id != player.id:
        raise HTTPException(
            status_code=409, detail="this telegram account is linked to another player"
        )
    await dao.player.link_user(player, saved)
    await dao.commit()
    return {"ok": True}


def setup() -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])
    router.add_api_route("/one-time-token", one_time_token_login, methods=["POST"])
    router.add_api_route("/token", login, methods=["POST"])
    router.add_api_route("/login", tg_login_page, response_class=HTMLResponse, methods=["GET"])
    router.add_api_route("/logout", logout, methods=["POST"])
    router.add_api_route("/login/data", tg_login_result, methods=["GET"])
    router.add_api_route("/login/data", tg_login_result_post, methods=["POST"])
    router.add_api_route("/login/webapp", webapp_login_result_post, methods=["POST"])
    router.add_api_route("/register/email", email_register, methods=["POST"])
    router.add_api_route("/login/email", email_login, methods=["POST"])
    router.add_api_route("/email/confirm", email_confirm, methods=["POST"])
    router.add_api_route("/email/resend", email_resend, methods=["POST"])
    router.add_api_route("/email/link", email_link, methods=["POST"])
    router.add_api_route("/forgot-password", forgot_password, methods=["POST"])
    router.add_api_route("/link/tg", link_tg, methods=["POST"])
    return router
