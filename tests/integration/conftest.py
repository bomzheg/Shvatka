import logging

import pytest
import pytest_asyncio
from aiogram import Dispatcher, Bot
from aiogram_dialog.test_tools import MockMessageManager
from aiogram_tests.mocked_bot import MockedBot
from alembic.command import upgrade
from alembic.config import Config as AlembicConfig
from dataclass_factory import Factory
from dishka import make_async_container, AsyncContainer
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shvatka.api.dependencies import AuthProvider, ApiConfigProvider
from shvatka.common import Paths
from shvatka.common import create_telegraph
from shvatka.core.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.config.models.db import DBConfig
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.infrastructure.db.factory import create_lock_factory
from shvatka.infrastructure.di import (
    ConfigProvider,
    DbProviderD,
    RedisProvider,
    GameProvider,
    PlayerProvider,
    TeamProvider,
)
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.main_factory import Telegraph
from shvatka.tgbot.main_factory import (
    create_only_dispatcher,
)
from shvatka.tgbot.main_factory import setup_handlers
from shvatka.tgbot.middlewares import setup_middlewares
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from tests.conftest import paths, event_loop, dcf, bot_config  # noqa: F401
from tests.fixtures.conftest import fixtures_resource_path  # noqa: F401
from tests.fixtures.db_provider import TestDbProvider
from tests.fixtures.file_storage import MemoryFileStorageProvider
from tests.fixtures.game_fixtures import game, finished_game  # noqa: F401
from tests.fixtures.player import harry, hermione, ron, author, draco  # noqa: F401
from tests.fixtures.scn_fixtures import simple_scn, complex_scn, three_lvl_scn  # noqa: F401
from tests.fixtures.team import gryffindor, slytherin  # noqa: F401
from tests.mocks.file_storage import MemoryFileStorage
from tests.mocks.game_log import GameLogWriterMock
from tests.mocks.scheduler_mock import SchedulerMock
from tests.mocks.user_getter import UserGetterMock

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session")
async def dishka():
    container = make_async_container(
        ConfigProvider("SHVATKA_TEST_PATH"),
        TestDbProvider(),
        ApiConfigProvider(),
        DbProviderD(),
        RedisProvider(),
        AuthProvider(),
        GameProvider(),
        PlayerProvider(),
        MemoryFileStorageProvider(),
        TeamProvider(),
    )
    yield container
    await container.close()


@pytest_asyncio.fixture(scope="session")
async def level_test_dao(dishka: AsyncContainer) -> LevelTestingData:
    return await dishka.get(LevelTestingData)


@pytest_asyncio.fixture
async def dishka_request(dishka: AsyncContainer):
    async with dishka() as request_container:
        yield request_container


@pytest_asyncio.fixture
async def dao(dishka_request: AsyncContainer) -> HolderDao:
    dao_ = await dishka_request.get(HolderDao)
    await clear_data(dao_)
    return dao_


@pytest_asyncio.fixture
async def check_dao(dishka: AsyncContainer):
    async with dishka() as request_container:
        yield await request_container.get(HolderDao)


async def clear_data(dao: HolderDao):
    await dao.poll.delete_all()
    await dao.achievement.delete_all()
    await dao.file_info.delete_all()
    await dao.organizer.delete_all()
    await dao.waiver.delete_all()
    await dao.level.delete_all()
    await dao.level_time.delete_all()
    await dao.key_time.delete_all()
    await dao.game.delete_all()
    await dao.team_player.delete_all()
    await dao.chat.delete_all()
    await dao.team.delete_all()
    await dao.user.delete_all()
    await dao.player.delete_all()
    await dao.commit()


@pytest.fixture(scope="session")
def scheduler():
    return SchedulerMock()


@pytest.fixture(scope="session")
def locker() -> KeyCheckerFactory:
    return create_lock_factory()


@pytest.fixture(scope="session")
def telegraph(bot_config: TgBotConfig) -> Telegraph:
    return create_telegraph(bot_config=bot_config.bot)


@pytest.fixture(scope="session")
def message_manager():
    return MockMessageManager()


@pytest_asyncio.fixture(scope="session")
async def dp(
    user_getter: UserGetter,
    dcf: Factory,
    scheduler: Scheduler,
    locker: KeyCheckerFactory,
    telegraph: Telegraph,
    message_manager: MockMessageManager,
    dishka: AsyncContainer,
) -> Dispatcher:
    bot_config = await dishka.get(TgBotConfig)
    dp = create_only_dispatcher(bot_config, await dishka.get(Redis))
    bg_factory = setup_handlers(dp, bot_config.bot, message_manager=message_manager)
    setup_middlewares(
        dp=dp,
        pool=await dishka.get(async_sessionmaker[AsyncSession]),
        config=bot_config,
        user_getter=user_getter,
        dcf=dcf,
        redis=await dishka.get(Redis),
        scheduler=scheduler,
        locker=locker,
        file_storage=await dishka.get(FileStorage),  # type: ignore[type-abstract]
        level_test_dao=await dishka.get(LevelTestingData),
        telegraph=telegraph,
        bg_manager_factory=bg_factory,
    )
    return dp


@pytest.fixture(scope="session")
def user_getter() -> UserGetter:
    return UserGetterMock()


@pytest_asyncio.fixture
async def bot(dishka: AsyncContainer) -> Bot:
    return MockedBot(token=(await dishka.get(TgBotConfig)).bot.token)


@pytest_asyncio.fixture(scope="session")
async def alembic_config(dishka: AsyncContainer, paths: Paths) -> AlembicConfig:
    alembic_cfg = AlembicConfig(str(paths.app_dir.parent / "alembic.ini"))
    alembic_cfg.set_main_option(
        "script_location",
        str(paths.app_dir.parent / "shvatka" / "infrastructure" / "db" / "migrations"),
    )
    db_config = await dishka.get(DBConfig)  # type: ignore[type-abstract]
    alembic_cfg.set_main_option("sqlalchemy.url", db_config.uri)
    return alembic_cfg


@pytest.fixture(scope="session", autouse=True)
def upgrade_schema_db(alembic_config: AlembicConfig):
    upgrade(alembic_config, "head")


@pytest_asyncio.fixture(scope="session")
async def file_storage(dishka: AsyncContainer) -> FileStorage:
    return await dishka.get(FileStorage)  # type: ignore[type-abstract]


@pytest.fixture
def hint_parser(
    dao: HolderDao,
    file_storage: FileStorage,
    bot: Bot,
) -> HintParser:
    return HintParser(dao=dao.file_info, file_storage=file_storage, bot=bot)


@pytest.fixture
def file_gateway(
    file_storage: FileStorage, bot: Bot, dao: HolderDao, bot_config: TgBotConfig
) -> FileGateway:
    return BotFileGateway(
        bot=bot,
        file_storage=file_storage,
        dao=dao.file_info,
        tech_chat_id=bot_config.bot.log_chat,
    )


@pytest.fixture
def game_log() -> GameLogWriter:
    return GameLogWriterMock()


@pytest.fixture(autouse=True)
def clean_up_memory(file_storage: MemoryFileStorage):
    file_storage.storage.clear()
