import dature
from dature import Absolute, F

from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source
from shvatka.common.config.parser.main import load_config as load_common_config
from shvatka.infrastructure.db.config.parser.storage import load_storage_config
from shvatka.tgbot.config.models.bot import TgClientConfig, BotConfig
from shvatka.tgbot.config.models.main import TgBotConfig


def load_config(paths: Paths) -> TgBotConfig:
    bot_config = load_bot_config(paths)
    return TgBotConfig.from_base(
        base=load_common_config(paths),
        bot=bot_config,
        storage=load_storage_config(paths),
        tg_client=TgClientConfig(bot_token=bot_config.token),
    )


def load_bot_config(paths: Paths) -> BotConfig:
    return dature.load(
        config_source(
            paths,
            prefix="bot",
            # superusers live at the top level of the config (shared by api and bot),
            # but BotConfig still exposes them for the bot's superuser handlers/filters.
            field_mapping={F[BotConfig].superusers: Absolute("superusers")},
        ),
        schema=BotConfig,
    )
