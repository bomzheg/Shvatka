from shvatka.common.factory import TelegraphProvider, DCFProvider
from shvatka.infrastructure.di.bot import BotProvider, GameLogProvider
from shvatka.infrastructure.di.config import ConfigProvider, DbConfigProvider
from shvatka.infrastructure.di.db import DbProvider, RedisProvider, LockProvider, DAOProvider
from shvatka.infrastructure.di.files import FileClientProvider
from shvatka.infrastructure.di.interactors import GamePlayProvider
from shvatka.infrastructure.scheduler.factory import SchedulerProvider


def get_providers(paths_env):
    return [
        ConfigProvider(paths_env),
        DbConfigProvider(),
        DbProvider(),
        TelegraphProvider(),
        DCFProvider(),
        DAOProvider(),
        RedisProvider(),
        FileClientProvider(),
        BotProvider(),
        GamePlayProvider(),
        SchedulerProvider(),
        GameLogProvider(),
        LockProvider(),
    ]
