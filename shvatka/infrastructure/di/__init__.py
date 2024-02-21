from shvatka.infrastructure.di.bot import BotProvider
from shvatka.infrastructure.di.config import ConfigProvider, DbConfigProvider
from shvatka.infrastructure.di.db import DbProviderD, RedisProvider
from shvatka.infrastructure.di.files import FileClientProvider
from shvatka.infrastructure.di.game import GameProvider
from shvatka.infrastructure.di.player import PlayerProvider
from shvatka.infrastructure.di.team import TeamProvider


def get_providers(paths_env):
    return [
        ConfigProvider(paths_env),
        DbConfigProvider(),
        DbProviderD(),
        RedisProvider(),
        GameProvider(),
        PlayerProvider(),
        FileClientProvider(),
        BotProvider(),
        TeamProvider(),
    ]
