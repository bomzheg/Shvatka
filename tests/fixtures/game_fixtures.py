from io import BytesIO

import pytest_asyncio
from dataclass_factory import Factory

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.services.game import upsert_game


@pytest_asyncio.fixture
async def game(
    complex_scn: dict, author: dto.Player, dao: HolderDao, dcf: Factory, file_storage: FileStorage,
) -> dto.FullGame:
    return await upsert_game(
        complex_scn,
        {"a3bc9b96-3bb8-4dbc-b996-ce1015e66e53": BytesIO(b"123")},
        author,
        dao.game_upserter,
        dcf,
        file_storage,
    )
