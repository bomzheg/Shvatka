import dature

from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source
from shvatka.tgbot.config.models.main import TgBotConfig


def load_config(paths: Paths) -> TgBotConfig:
    return dature.load(config_source(paths), schema=TgBotConfig)
