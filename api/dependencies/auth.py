import logging
from datetime import timedelta, datetime

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette import status

from api.dependencies.db import dao_provider
from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.utils.exceptions import NoUsernameFound

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def get_current_user():
    raise NotImplementedError


class AuthProvider:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # to get a string like this run:
        # openssl rand -hex 32
        self.secret_key = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        self.algorythm = "HS256"
        self.access_token_expire_minutes = 30

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    async def authenticate_user(self, username: str, password: str, dao: HolderDao) -> dto.User | None:
        try:
            user = await dao.user.get_by_username(username)
        except NoUsernameFound:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorythm)
        return encoded_jwt

    async def get_current_user(self, token: str = Depends(oauth2_scheme), dao: HolderDao = Depends(dao_provider)):
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
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        try:
            user = await dao.user.get_by_username(username=token_data.username)
        except NoUsernameFound:
            raise credentials_exception
        return user

    async def login(self, form_data: OAuth2PasswordRequestForm = Depends(), dao: HolderDao = Depends(dao_provider)):
        user = await self.authenticate_user(form_data.username, form_data.password, dao)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
