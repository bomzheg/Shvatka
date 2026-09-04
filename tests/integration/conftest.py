import logging
import typing
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram_dialog.api.protocols import MessageManagerProtocol
from alembic.command import upgrade
from alembic.config import Config as AlembicConfig
from dishka import STRICT_VALIDATION, AsyncContainer, make_async_container
from telegraph.aio import Telegraph

from shvatka.common import Paths
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.clients.file_storage import LocalFileStorage
from shvatka.infrastructure.db.config.models.db import DBConfig
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from tests.fixtures.di import get_test_providers
from tests.mocks.datetime_mock import ClockMock
from tests.mocks.file_gateway import FakeTelegram
from tests.mocks.file_storage import MemoryFileStorage
from tests.mocks.game_log import GameLogWriterMock

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session")
async def dishka():
    container = make_async_container(
        *get_test_providers(),
        validation_settings=STRICT_VALIDATION,
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
    await dao.level_file.delete_all()
    await dao.game_file.delete_all()
    await dao.file_info.delete_all()
    await dao.organizer.delete_all()
    await dao.waiver.delete_all()
    await dao.level.delete_all()
    await dao.key_time.delete_all()
    await dao.timers.delete_all()
    await dao.events.delete_all()
    await dao.level_time.delete_all()
    await dao.game.delete_all()
    await dao.team_player.delete_all()
    await dao.chat.delete_all()
    await dao.team.delete_all()
    await dao.user.delete_all()
    await dao.email.delete_all()
    await dao.player.delete_all()
    await dao.commit()


@pytest_asyncio.fixture(scope="session")
async def scheduler(dishka: AsyncContainer) -> Scheduler:
    return await dishka.get(Scheduler)


@pytest_asyncio.fixture(scope="session")
async def locker(dishka: AsyncContainer) -> KeyCheckerFactory:
    return await dishka.get(KeyCheckerFactory)


@pytest_asyncio.fixture(scope="session")
async def telegraph(dishka: AsyncContainer) -> Telegraph:
    return await dishka.get(Telegraph)


@pytest_asyncio.fixture(scope="session")
async def message_manager(dishka: AsyncContainer) -> MessageManagerProtocol:
    return await dishka.get(MessageManagerProtocol)


@pytest_asyncio.fixture(scope="session")
async def dp(dishka: AsyncContainer) -> Dispatcher:
    return await dishka.get(Dispatcher)


@pytest_asyncio.fixture(scope="session")
async def user_getter(dishka: AsyncContainer) -> UserGetter:
    return await dishka.get(UserGetter)


@pytest_asyncio.fixture
async def bot(dishka: AsyncContainer) -> Bot:
    return await dishka.get(Bot)


@pytest_asyncio.fixture(scope="session")
async def alembic_config(dishka: AsyncContainer, paths: Paths) -> AlembicConfig:
    alembic_cfg = AlembicConfig(str(paths.app_dir.parent / "alembic.ini"))
    alembic_cfg.set_main_option(
        "script_location",
        str(paths.app_dir.parent / "shvatka" / "infrastructure" / "db" / "migrations"),
    )
    db_config = await dishka.get(DBConfig)
    alembic_cfg.set_main_option("sqlalchemy.url", db_config.uri)
    return alembic_cfg


@pytest.fixture(scope="session", autouse=True)
def upgrade_schema_db(alembic_config: AlembicConfig):
    upgrade(alembic_config, "head")


@pytest_asyncio.fixture(scope="session")
async def file_storage(dishka: AsyncContainer) -> MemoryFileStorage:
    return await dishka.get(MemoryFileStorage)


@pytest_asyncio.fixture(scope="session")
async def local_storage(dishka: AsyncContainer) -> LocalFileStorage:
    return await dishka.get(LocalFileStorage)


@pytest.fixture
def hint_parser(
    dao: HolderDao,
    file_storage: MemoryFileStorage,
    bot: Bot,
) -> HintParser:
    return HintParser(dao=dao.file_info, file_storage=file_storage, bot=bot)


@pytest_asyncio.fixture
async def file_gateway(dishka_request: AsyncContainer) -> FileGateway:
    return await dishka_request.get(FileGateway)


@pytest_asyncio.fixture
async def game_log(dishka: AsyncContainer) -> GameLogWriterMock:
    return await dishka.get(GameLogWriterMock)


@pytest_asyncio.fixture
async def telegram(dishka: AsyncContainer) -> FakeTelegram:
    return await dishka.get(FakeTelegram)


@pytest.fixture(autouse=True)
def clean_up_telegram(telegram: FakeTelegram):
    telegram.clear()


@pytest.fixture(autouse=True)
def clean_up_memory(file_storage: MemoryFileStorage):
    file_storage.storage.clear()
    file_storage.modified_at.clear()


@pytest.fixture(autouse=True)
def clean_up_game_log(game_log: GameLogWriterMock):
    game_log.requests.clear()


@pytest_asyncio.fixture
async def clock(dishka: AsyncContainer) -> ClockMock:
    return await dishka.get(ClockMock)


@pytest_asyncio.fixture(scope="session")
async def bot_session(dishka: AsyncContainer) -> BaseSession:
    return await dishka.get(BaseSession)


@pytest.fixture(autouse=True)
def clean_up_bot_session(bot_session: BaseSession):
    session = typing.cast(MagicMock, bot_session)
    session.reset_mock(return_value=True, side_effect=True)
