from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from app.models.config.db import DBConfig


@dataclass
class Config:
    paths: Paths
    db: DBConfig
    bot: BotConfig

    @property
    def app_dir(self) -> Path:
        return self.paths.app_dir

    @property
    def config_path(self) -> Path:
        return self.paths.config_path

    @property
    def log_path(self) -> Path:
        return self.paths.log_path


@dataclass
class Paths:
    app_dir: Path

    @property
    def config_path(self) -> Path:
        return self.app_dir / "config"

    @property
    def logging_config_file(self) -> Path:
        return self.config_path / "logging.yaml"

    @property
    def log_path(self) -> Path:
        return self.app_dir / "log"


@dataclass
class BotConfig:
    token: str
    log_chat: int
    superusers: list[int]
    bot_api: BotApiConfig

    def create_session(self) -> AiohttpSession | None:
        if self.bot_api.is_local:
            return AiohttpSession(api=self.bot_api.create_server())
        return None


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
