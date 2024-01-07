from dataclass_factory import Factory, Schema, NameStyle

from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_file_reader import read_config
from shvatka.common.config.parser.main import load_config as load_common_config
from shvatka.infrastructure.db.config.parser.storage import load_storage_config
from shvatka.tgbot.config.models.bot import TgClientConfig, BotConfig
from shvatka.tgbot.config.models.main import TgBotConfig


def load_config(paths: Paths) -> TgBotConfig:
    dcf = Factory(default_schema=Schema(name_style=NameStyle.kebab))
    config_dct = read_config(paths)

    bot_config = dcf.load(config_dct["bot"], BotConfig)
    return TgBotConfig.from_base(
        base=load_common_config(config_dct, paths, dcf),
        bot=bot_config,
        storage=load_storage_config(config_dct["storage"]),
        tg_client=TgClientConfig(bot_token=bot_config.token),
    )
