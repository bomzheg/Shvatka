import pytest_asyncio
from dataclass_factory import Factory

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.models.dto.scn.game import RawGameScenario
from shvatka.services.game import upsert_game


@pytest_asyncio.fixture
async def game(
    complex_scn: RawGameScenario, author: dto.Player, dao: HolderDao, dcf: Factory, file_storage: FileStorage,
) -> dto.FullGame:
    return await upsert_game(
        complex_scn,
        author,
        dao.game_upserter,
        dcf,
        file_storage,
    )
