from dataclasses import dataclass
from typing import Type

from fastapi import HTTPException
from jose import JWTError
from starlette.requests import Request

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.utils.cookie_auth import OAuth2PasswordBearerWithCookie
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services.player import upsert_player, get_my_team
from shvatka.core.services.team import get_by_chat
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao

sentinel = object()

@dataclass(kw_only=True)
class ApiIdentityProvider(IdentityProvider):
    request: Request
    cookie_auth: OAuth2PasswordBearerWithCookie
    auth_properties: AuthProperties
    dao: HolderDao
    user: dto.User | None | Type[sentinel] = sentinel
    player: dto.Player | None | Type[sentinel] = sentinel
    team: dto.Team | None | Type[sentinel] = sentinel
    chat: dto.Chat | None | Type[sentinel] = sentinel

    async def get_user(self) -> dto.User:
        if self.user is None:
            raise HTTPException(status_code=401)
        if self.user is not sentinel:
            return self.user
        try:
            token = self.cookie_auth.get_token(self.request)
            self.user = await self.auth_properties.get_current_user(token, self.dao)
        except (JWTError, HTTPException):
            user = await self.auth_properties.get_user_basic(self.request, self.dao)
            self.user = user
            if user is None:
                raise
        return self.user

    async def get_player(self) -> dto.Player:
        if self.player is None:
            raise HTTPException(status_code=401)
        if self.player is not sentinel:
            return self.player
        self.player = await upsert_player(await self.get_user(), self.dao.player)
        return self.player

    async def get_team(self) -> dto.Team:
        player = await self.get_player()
        if self.team is None:
            raise exceptions.PlayerNotInTeam(player=player)
        if self.team is not sentinel:
            return self.team
        team = await get_my_team(player, self.dao.team_player)
        self.team = team
        if team is None:
            raise exceptions.PlayerNotInTeam(player=player)
        return team

    async def get_chat(self) -> dto.Chat:
        if self.chat is None:
            raise HTTPException(status_code=401)
        if self.chat is not sentinel:
            return self.chat
        team = await self.get_team()
        if team.has_chat():
            return await self.dao.chat.get_by_tg_id(team.get_chat_id())
        else:
            raise exceptions.ChatNotFound(team=team)


