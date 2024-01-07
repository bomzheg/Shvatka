from __future__ import annotations

import secrets
from dataclasses import dataclass
from enum import Enum

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer


@dataclass
class BotConfig:
    token: str
    log_chat: int
    """tech chat for tech logs"""
    game_log_chat: int
    """game log for major game events notifications"""
    superusers: list[int]
    bot_api: BotApiConfig
    telegraph_token: str
    webhook: WebhookConfig

    def create_session(self) -> AiohttpSession | None:
        if self.bot_api.is_local:
            return AiohttpSession(api=self.bot_api.create_server())
        return None


@dataclass
class TgClientConfig:
    bot_token: str
    api_hash: str = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
    api_id: int = 6


@dataclass
class BotApiConfig:
    type: BotApiType
    botapi_url: str | None
    botapi_file_url: str | None

    @property
    def is_local(self) -> bool:
        return self.type == BotApiType.local

    def create_server(self) -> TelegramAPIServer:
        if self.type != BotApiType.local:
            raise RuntimeError("can create only local botapi server")
        return TelegramAPIServer(
            base=f"{self.botapi_url}/bot{{token}}/{{method}}",
            file=f"{self.botapi_file_url}{{path}}",
        )


class BotApiType(Enum):
    official = "official"
    local = "local"


@dataclass
class WebhookConfig:
    web_url: str
    local_url: str
    path: str
    secret: str = secrets.token_urlsafe(32)
