from dataclass_factory import Factory, Schema, NameStyle

from src.common.config.models.paths import Paths
from src.common.config.parser.config_file_reader import read_config
from src.common.config.parser.main import load_config as load_common_config
from src.infrastructure.db.config.parser.storage import load_storage_config
from src.tgbot.config.models.bot import TgClientConfig
from src.tgbot.config.models.main import TgBotConfig
from src.tgbot.config.parser.bot import load_bot_config


def load_config(paths: Paths) -> TgBotConfig:
    dcf = Factory(default_schema=Schema(name_style=NameStyle.kebab))
    config_dct = read_config(paths)

    bot_config = load_bot_config(config_dct["bot"])
    return TgBotConfig.from_base(
        base=load_common_config(config_dct, paths, dcf),
        bot=bot_config,
        storage=load_storage_config(config_dct["storage"]),
        tg_client=TgClientConfig(bot_token=bot_config.token),
    )
