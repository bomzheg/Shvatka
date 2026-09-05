from shvatka.common.factory import DCFProvider, UrlProvider
from shvatka.infrastructure.db.factory import LockProvider
from shvatka.infrastructure.di.bot import BotProvider
from shvatka.infrastructure.di.config import ConfigProvider, DbConfigProvider
from shvatka.infrastructure.di.db import (
    ComplexDaoProvider,
    DAOProvider,
    DbProvider,
    RedisProvider,
)
from shvatka.infrastructure.di.files import FileClientProvider
from shvatka.infrastructure.di.interactors import (
    ContextProvider,
    GamePlayProvider,
    GameReleaseProvider,
    NotificationProvider,
    PlayerProvider,
    RequestProvider,
    SearchProvider,
    TeamProvider,
    WaiverProvider,
)
from shvatka.infrastructure.di.mail import EmailInteractorProvider, MailProvider
from shvatka.infrastructure.di.printer import PrinterProvider
from shvatka.infrastructure.nursery import NurseryProvider
from shvatka.infrastructure.scheduler.factory import SchedulerProvider


def get_providers(paths_env):
    return [
        ConfigProvider(paths_env),
        DbConfigProvider(),
        DbProvider(),
        UrlProvider(),
        DCFProvider(),
        DAOProvider(),
        ComplexDaoProvider(),
        RedisProvider(),
        FileClientProvider(),
        MailProvider(),
        EmailInteractorProvider(),
        BotProvider(),
        ContextProvider(),
        GamePlayProvider(),
        GameReleaseProvider(),
        WaiverProvider(),
        PlayerProvider(),
        TeamProvider(),
        NotificationProvider(),
        RequestProvider(),
        SearchProvider(),
        PrinterProvider(),
        LockProvider(),
        NurseryProvider(),
        SchedulerProvider(),
    ]
