from shvatka.infrastructure.di.bot import BotProvider
from shvatka.infrastructure.di.config import ConfigProvider, DbConfigProvider
from shvatka.infrastructure.di.db import DbProvider, RedisProvider
from shvatka.infrastructure.di.files import FileClientProvider
from shvatka.infrastructure.di.game import GameProvider
from shvatka.infrastructure.di.interactors import DAOProvider, InteractorProvider


def get_providers(paths_env):
    return [
        ConfigProvider(paths_env),
        DbConfigProvider(),
        DbProvider(),
        RedisProvider(),
        GameProvider(),
        FileClientProvider(),
        BotProvider(),
        DAOProvider(),
        InteractorProvider(),
    ]
