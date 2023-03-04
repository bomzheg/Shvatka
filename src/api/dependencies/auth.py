import hashlib
import hmac
import logging
from datetime import timedelta, datetime

from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from starlette import status
from starlette.responses import HTMLResponse

from src.api.config.models.auth import AuthConfig
from src.api.dependencies.db import dao_provider
from src.api.models.auth import UserTgAuth, Token
from src.core.models import dto
from src.core.services.user import upsert_user
from src.core.utils.datetime_utils import tz_utc
from src.core.utils.exceptions import NoUsernameFound
from src.infrastructure.db.dao.holder import HolderDao

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
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user() -> dto.User:
    raise NotImplementedError


class AuthProvider:
    def __init__(self, config: AuthConfig):
        self.config = config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # to get a string like this run:
        # openssl rand -hex 32
        self.secret_key = config.secret_key
        self.algorythm = "HS256"
        self.access_token_expire = config.token_expire
        self.router = APIRouter()
        self.setup_auth_routes()

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
        except NoUsernameFound:
            raise http_status_401
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
            data={"sub": user.username}, expires_delta=self.access_token_expire
        )

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        dao: HolderDao = Depends(dao_provider),
    ) -> dto.User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorythm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        try:
            user = await dao.user.get_by_username(username=username)
        except NoUsernameFound:
            raise credentials_exception
        return user

    async def login(
        self,
        form_data: OAuth2PasswordRequestForm = Depends(),
        dao: HolderDao = Depends(dao_provider),
    ) -> Token:
        user = await self.authenticate_user(form_data.username, form_data.password, dao)
        return self.create_user_token(user)

    async def tg_login_page(self):
        return TG_WIDGET_HTML.format(
            bot_username=self.config.bot_username,
            auth_url=self.config.auth_url,
        )

    async def tg_login_result(
        self,
        user: UserTgAuth = Depends(),
        dao: HolderDao = Depends(dao_provider),
    ) -> Token:
        check_tg_hash(user, self.config.bot_token)
        await upsert_user(user.to_dto(), dao.user)
        return self.create_user_token(user.to_dto())

    def setup_auth_routes(self):
        self.router.add_api_route("/auth/token", self.login, methods=["POST"])
        self.router.add_api_route(
            "/auth/login", self.tg_login_page, response_class=HTMLResponse, methods=["GET"]
        )
        self.router.add_api_route("/auth/login/data", self.tg_login_result, methods=["GET"])


def check_tg_hash(user: UserTgAuth, bot_token: str):
    data_check = user.to_tg_spec().encode("utf-8")
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    hmac_string = hmac.new(secret_key, data_check, hashlib.sha256).hexdigest()
    if hmac_string != user.hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="something wrong")
