from shvatka.infrastructure.di.bot import BotProvider
from shvatka.infrastructure.di.config import ConfigProvider, DbConfigProvider
from shvatka.infrastructure.di.db import DbProvider, RedisProvider, DAOProvider
from shvatka.infrastructure.di.files import FileClientProvider
from shvatka.infrastructure.di.interactors import GamePlayProvider
from shvatka.infrastructure.di.printer import PrinterProvider


def get_providers(paths_env):
    return [
        ConfigProvider(paths_env),
        DbConfigProvider(),
        DbProvider(),
        DAOProvider(),
        RedisProvider(),
        FileClientProvider(),
        BotProvider(),
        GamePlayProvider(),
        PrinterProvider(),
    ]
