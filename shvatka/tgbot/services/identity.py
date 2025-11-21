from typing import TypedDict, cast

from aiogram import types
from aiogram.types import TelegramObject
from aiogram_dialog.api.entities import DialogUpdate
from dishka.integrations.aiogram import AiogramMiddlewareData

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services.chat import upsert_chat
from shvatka.core.services.player import upsert_player, get_full_team_player
from shvatka.core.services.team import get_by_chat
from shvatka.core.services.user import upsert_user
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.utils.data import SHMiddlewareData


class LoadedData(TypedDict, total=False):
    user: dto.User | None
    chat: dto.Chat | None
    player: dto.Player | None
    team: dto.Team | None
    full_team_player: dto.FullTeamPlayer | None


class TgBotIdentityProvider(IdentityProvider):
    def __init__(
        self,
        *,
        dao: HolderDao,
        event: TelegramObject,
        aiogram_data: AiogramMiddlewareData,
    ) -> None:
        self.dao = dao
        self.event = event
        self.aiogram_data = aiogram_data
        self.cache = LoadedData()

    async def get_user(self) -> dto.User | None:
        data = cast(SHMiddlewareData, self.aiogram_data)
        if "user" in self.cache:
            return self.cache["user"]
        if isinstance(self.event, DialogUpdate):
            user_tg: types.User | None
            if user_tg := data.get("event_from_user", None):
                user = await self.dao.user.get_by_tg_id(user_tg.id)
            else:
                user = None
        else:
            user = await save_user(data, self.dao)
        self.cache["user"] = user
        return user

    async def get_chat(self) -> dto.Chat | None:
        data = cast(SHMiddlewareData, self.aiogram_data)
        if "chat" in self.cache:
            return self.cache["chat"]
        if isinstance(self.event, DialogUpdate):
            chat_tg: types.Chat | None
            if chat_tg := data.get("event_chat", None):
                chat = await self.dao.chat.get_by_tg_id(chat_tg.id)
            else:
                chat = None
        else:
            chat = await save_chat(data, self.dao)
        self.cache["chat"] = chat
        return chat

    async def get_player(self) -> dto.Player | None:
        if "player" in self.cache:
            return self.cache["player"]
        player = await save_player(await self.get_user(), self.dao)
        self.cache["player"] = player
        return player

    async def get_team(self) -> dto.Team | None:
        if "team" in self.cache:
            return self.cache["team"]
        team = await load_team(await self.get_chat(), self.dao)
        self.cache["team"] = team
        return team

    async def get_full_team_player(self) -> dto.FullTeamPlayer | None:
        if "full_team_player" in self.cache:
            return self.cache["full_team_player"]
        player = await self.get_player()
        if player is None:
            self.cache["full_team_player"] = None
            return None
        try:
            team_player = await get_full_team_player(
                player, await self.get_team(), dao=self.dao.team_player
            )
        except exceptions.PlayerNotInTeam:
            self.cache["full_team_player"] = None
            return None
        self.cache["full_team_player"] = team_player
        return team_player


async def save_user(data: SHMiddlewareData, holder_dao: HolderDao) -> dto.User | None:
    user = data.get("event_from_user", None)
    if not user:
        return None
    return await upsert_user(dto.User.from_aiogram(user), holder_dao.user)


async def save_player(user: dto.User | None, holder_dao: HolderDao) -> dto.Player | None:
    if not user:
        return None
    return await upsert_player(user, holder_dao.player)


async def save_chat(data: SHMiddlewareData, holder_dao: HolderDao) -> dto.Chat | None:
    chat = data.get("event_chat", None)
    if not chat:
        return None
    return await upsert_chat(dto.Chat.from_aiogram(chat), holder_dao.chat)


async def load_team(chat: dto.Chat | None, holder_dao: HolderDao) -> dto.Team | None:
    if not chat:
        return None
    return await get_by_chat(chat, holder_dao.team)
