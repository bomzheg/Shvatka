from __future__ import annotations

from dataclasses import dataclass

from shvatka.common.config.models.main import Config
from shvatka.infrastructure.db.config.models.storage import StorageConfig
from shvatka.tgbot.config.models.bot import BotConfig


@dataclass(kw_only=True)
class TgBotConfig(Config):
    bot: BotConfig
    storage: StorageConfig
