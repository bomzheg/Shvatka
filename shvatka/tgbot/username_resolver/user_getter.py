from __future__ import annotations

import asyncio
import logging

import pyrogram
from aiogram.types import User
from pyrogram import Client
from pyrogram.errors import RPCError, UsernameNotOccupied, FloodWait

from shvatka.core.utils.exceptions import UsernameResolverError, NoUsernameFound
from shvatka.tgbot.config.models.bot import TgClientConfig

logger = logging.getLogger(__name__)
SLEEP_TIME = 50


class UserGetter:
    def __init__(self, client_config: TgClientConfig) -> None:
        self._client_api_bot = Client(
            "shvatka_bot",
            bot_token=client_config.bot_token,
            api_id=client_config.api_id,
            api_hash=client_config.api_hash,
            no_updates=True,
        )

    async def get_user(self, username: str | None = None) -> User | None:
        try:
            return await self.get_user_by_username(username)
        except RPCError:
            return None

    async def get_user_by_username(self, username: str) -> User:
        logger.info("get user of username %s", username)
        try:
            user = await self._client_api_bot.get_users(username)
        except UsernameNotOccupied as e:
            logger.info("Username not found %s", username)
            raise NoUsernameFound(username=username) from e
        except FloodWait as e:
            logger.error("Flood Wait %s", e, exc_info=e)
            await asyncio.sleep(e.value)
            raise UsernameResolverError(username=username) from e
        except Exception as e:
            raise UsernameResolverError(username=username) from e
        as_aio = map_pyrogram_user_to_aiogram(user)
        logger.info("found user %s", as_aio.json())
        return as_aio

    async def start(self):
        if not self._client_api_bot.is_connected:
            await self._client_api_bot.start()

    async def stop(self):
        if self._client_api_bot.is_connected:
            await self._client_api_bot.stop()

    async def __aenter__(self) -> UserGetter:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


def map_pyrogram_user_to_aiogram(user: pyrogram.types.User) -> User:
    return User(
        id=user.id,
        is_bot=user.is_bot,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
    )
