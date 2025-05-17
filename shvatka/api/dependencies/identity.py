from dataclasses import dataclass, field
from typing import cast, TypedDict

from fastapi import HTTPException
from jose import JWTError
from starlette.requests import Request

from shvatka.api.dependencies.auth import AuthProperties
from shvatka.api.utils.cookie_auth import OAuth2PasswordBearerWithCookie
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services.player import upsert_player, get_my_team
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao

sentinel = object()


class LoadedData(TypedDict, total=False):
    user: dto.User | None
    chat: dto.Chat | None
    player: dto.Player | None
    team: dto.Team | None


@dataclass(kw_only=True)
class ApiIdentityProvider(IdentityProvider):
    request: Request
    cookie_auth: OAuth2PasswordBearerWithCookie
    auth_properties: AuthProperties
    dao: HolderDao
    cache: LoadedData = field(default_factory=LoadedData)  # type: ignore[arg-type]

    async def get_user(self) -> dto.User | None:
        if "user" in self.cache:
            if self.cache["user"] is None:
                raise HTTPException(status_code=401)
            return self.cache["user"]
        user: dto.User | None
        try:
            token = self.cookie_auth.get_token(self.request)
            user = await self.auth_properties.get_current_user(token, self.dao)
        except (JWTError, HTTPException):
            user = await self.auth_properties.get_user_basic(self.request, self.dao)
        self.cache["user"] = user
        if user is None:
            raise
        return user

    async def get_player(self) -> dto.Player:
        if "player" in self.cache:
            if self.cache["player"] is None:
                raise HTTPException(status_code=401)
            return self.cache["player"]
        player = await upsert_player(await self.get_required_user(), self.dao.player)
        self.cache["player"] = player
        return player

    async def get_team(self) -> dto.Team:
        player = await self.get_player()
        if "team" in self.cache:
            if self.cache["team"] is None:
                raise exceptions.PlayerNotInTeam(player=player)
            return self.cache["team"]
        team = await get_my_team(player, self.dao.team_player)
        self.cache["team"] = team
        if team is None:
            raise exceptions.PlayerNotInTeam(player=player)
        return team

    async def get_chat(self) -> dto.Chat:
        if "chat" in self.cache:
            if self.cache["chat"] is None:
                raise HTTPException(status_code=401)
            return self.cache["chat"]
        team = await self.get_team()
        if team.has_chat():
            chat = await self.dao.chat.get_by_tg_id(cast(int, team.get_chat_id()))
            self.cache["chat"] = chat
            return chat
        else:
            raise exceptions.ChatNotFound(team=team)
