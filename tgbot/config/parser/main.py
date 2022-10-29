from common.config.models.paths import Paths
from common.config.parser.config_file_reader import read_config
from common.config.parser.main import load_config as load_common_config
from db.config.parser.storage import load_storage_config
from tgbot.config.models.bot import TgClientConfig
from tgbot.config.models.main import TgBotConfig
from tgbot.config.parser.bot import load_bot_config


def load_config(paths: Paths) -> TgBotConfig:
    config_dct = read_config(paths)

    bot_config = load_bot_config(config_dct["bot"])
    return TgBotConfig.from_base(
        base=load_common_config(config_dct, paths),
        bot=bot_config,
        storage=load_storage_config(config_dct["storage"]),
        tg_client=TgClientConfig(bot_token=bot_config.token),
    )
