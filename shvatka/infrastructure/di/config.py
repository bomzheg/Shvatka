from dishka import Provider, provide, Scope

from shvatka.api.config.models.auth import AuthConfig
from shvatka.api.config.models.main import ApiConfig
from shvatka.api.config.parser.main import load_config as load_api_config
from shvatka.common import FileStorageConfig, Paths, Config
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.infrastructure.db.config.models.db import RedisConfig, DBConfig
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.config.parser.main import load_config as load_bot_config


class ConfigProvider(Provider):
    scope = Scope.APP

    def __init__(self, path_env: str = "SHVATKA_PATH"):
        super().__init__()
        self.path_env = path_env

    @provide
    def get_paths(self) -> Paths:
        return common_get_paths(self.path_env)

    @provide
    def get_tgbot_config(self, paths: Paths) -> TgBotConfig:
        return load_bot_config(paths)

    @provide
    def get_base_config(self, config: TgBotConfig) -> Config:
        return config

    @provide
    def get_file_storage_config(self, config: Config) -> FileStorageConfig:
        return config.file_storage_config

    @provide
    def get_bot_config(self, config: TgBotConfig) -> BotConfig:
        return config.bot


class DbConfigProvider(Provider):
    scope = Scope.APP

    @provide
    def get_redis_config(self, config: Config) -> RedisConfig:
        return config.redis

    @provide
    def get_db_config(self, config: Config) -> DBConfig:
        return config.db
