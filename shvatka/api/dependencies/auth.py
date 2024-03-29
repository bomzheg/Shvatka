import hashlib
import hmac
import logging
import typing
from datetime import timedelta, datetime

from dishka import Provider, provide, Scope, from_context
from fastapi import HTTPException, Request
from jose import jwt, JWTError
from passlib.context import CryptContext
from starlette import status

from shvatka.api.config.models.auth import AuthConfig
from shvatka.api.models.auth import UserTgAuth, Token
from shvatka.api.utils.cookie_auth import OAuth2PasswordBearerWithCookie
from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.exceptions import NoUsernameFound
from shvatka.infrastructure.db.dao.holder import HolderDao


logger = logging.getLogger(__name__)


class AuthProperties:
    def __init__(self, config: AuthConfig) -> None:
        super().__init__()
        self.config = config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # to get a string like this run:
        # openssl rand -hex 32
        self.secret_key = config.secret_key
        self.algorythm = "HS256"
        self.access_token_expire = config.token_expire

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    async def authenticate_user(self, username: str, password: str, dao: HolderDao) -> dto.User:
        http_status_401 = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            user = await dao.user.get_by_username_with_password(username)
        except NoUsernameFound as e:
            raise http_status_401 from e
        if not self.verify_password(password, user.hashed_password or ""):
            raise http_status_401
        return user.without_password()

    def create_access_token(self, data: dict, expires_delta: timedelta) -> Token:
        to_encode = data.copy()
        expire = datetime.now(tz=tz_utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorythm)
        return Token(access_token=encoded_jwt, token_type="bearer")

    def create_user_token(self, user: dto.User) -> Token:
        return self.create_access_token(
            data={"sub": str(user.db_id)}, expires_delta=self.access_token_expire
        )

    async def get_current_user(
        self,
        token: Token,
        dao: HolderDao,
    ) -> dto.User:
        logger.debug("try to check token %s", token)
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token.access_token,
                self.secret_key,
                algorithms=[self.algorythm],
            )
            if payload.get("sub") is None:
                logger.warning("valid jwt contains no user id")
                raise credentials_exception
            user_db_id = int(typing.cast(str, payload.get("sub")))
        except JWTError as e:
            logger.info("invalid jwt", exc_info=e)
            raise credentials_exception from e
        except Exception as e:
            logger.warning("some jwt error", exc_info=e)
            raise
        try:
            user = await dao.user.get_by_id(user_db_id)
        except Exception as e:
            logger.info("user by id %s not found", user_db_id)
            raise credentials_exception from e
        return user


class AuthProvider(Provider):
    scope = Scope.APP
    request = from_context(provides=Request)

    @provide
    def get_auth_properties(self, config: AuthConfig) -> AuthProperties:
        return AuthProperties(config)

    @provide
    def get_cookie_auth(self) -> OAuth2PasswordBearerWithCookie:
        return OAuth2PasswordBearerWithCookie(token_url="auth/token")

    @provide(scope=Scope.REQUEST)
    async def get_token(
        self, request: Request, cookie_auth: OAuth2PasswordBearerWithCookie
    ) -> Token:
        return cookie_auth.get_token(request)

    @provide(scope=Scope.REQUEST)
    async def get_current_user(
        self,
        token: Token,
        auth_properties: AuthProperties,
        dao: HolderDao,
    ) -> dto.User:
        return await auth_properties.get_current_user(token, dao)


def check_tg_hash(user: UserTgAuth, bot_token: str):
    data_check = user.to_tg_spec().encode("utf-8")
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    hmac_string = hmac.new(secret_key, data_check, hashlib.sha256).hexdigest()
    if hmac_string != user.hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="something wrong")
