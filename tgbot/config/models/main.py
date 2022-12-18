from __future__ import annotations

from dataclasses import dataclass

from common.config.models.main import Config
from infrastructure.db.config.models.storage import StorageConfig
from tgbot.config.models.bot import BotConfig, TgClientConfig


@dataclass
class TgBotConfig(Config):
    bot: BotConfig
    storage: StorageConfig
    tg_client: TgClientConfig

    @classmethod
    def from_base(
        cls,
        base: Config,
        bot: BotConfig,
        storage: StorageConfig,
        tg_client: TgClientConfig,
    ):
        return cls(
            paths=base.paths,
            db=base.db,
            redis=base.redis,
            bot=bot,
            storage=storage,
            tg_client=tg_client,
            file_storage_config=base.file_storage_config,
        )
