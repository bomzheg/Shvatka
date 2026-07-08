from shvatka.common.factory import UrlProvider
from shvatka.infrastructure.di.bot import BotProvider
from shvatka.infrastructure.di.config import ConfigProvider, DbConfigProvider
from shvatka.infrastructure.di.db import DbProvider, RedisProvider, DAOProvider
from shvatka.infrastructure.di.files import FileClientProvider
from shvatka.infrastructure.di.mail import MailProvider, EmailInteractorProvider
from shvatka.infrastructure.di.interactors import GamePlayProvider, ContextProvider
from shvatka.infrastructure.di.interactors import WaiverProvider, PlayerProvider, TeamProvider
from shvatka.infrastructure.di.printer import PrinterProvider
from shvatka.infrastructure.db.factory import LockProvider
from shvatka.infrastructure.scheduler.factory import SchedulerProvider


def get_providers(paths_env):
    return [
        ConfigProvider(paths_env),
        DbConfigProvider(),
        DbProvider(),
        UrlProvider(),
        DAOProvider(),
        RedisProvider(),
        FileClientProvider(),
        MailProvider(),
        EmailInteractorProvider(),
        BotProvider(),
        ContextProvider(),
        GamePlayProvider(),
        WaiverProvider(),
        PlayerProvider(),
        TeamProvider(),
        PrinterProvider(),
        LockProvider(),
        SchedulerProvider(),
    ]
