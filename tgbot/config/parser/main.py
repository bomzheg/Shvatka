import yaml

from db.config.parser.db import load_db_config, load_redis_config
from db.config.parser.storage import load_storage_config
from tgbot.config.models.bot import TgClientConfig
from tgbot.config.models.main import Config, Paths
from tgbot.config.parser.bot import load_bot_config


def load_config(paths: Paths) -> Config:
    with (paths.config_path / "config.yml").open("r") as f:
        config_dct = yaml.safe_load(f)

    bot_config = load_bot_config(config_dct["bot"])
    return Config(
        paths=paths,
        db=load_db_config(config_dct["db"]),
        bot=bot_config,
        storage=load_storage_config(config_dct["storage"]),
        tg_client=TgClientConfig(bot_token=bot_config.token),
        redis=load_redis_config(config_dct["redis"]),
    )
