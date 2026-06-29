from copy import deepcopy
from io import BytesIO

import pytest
from adaptix import Retort
from sqlalchemy import select

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.services.game import upsert_game
from shvatka.infrastructure.db import models
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID


async def _level_file_ids(dao: HolderDao, level_id: int) -> set[int]:
    result = await dao.session.scalars(
        select(models.LevelFile.file_id).where(models.LevelFile.level_id == level_id)
    )
    return set(result.all())


async def _game_file_ids(dao: HolderDao, game_id: int) -> set[int]:
    result = await dao.session.scalars(
        select(models.GameFile.file_id).where(models.GameFile.game_id == game_id)
    )
    return set(result.all())


async def _file_id_by_guid(dao: HolderDao, guid: str) -> int:
    file_id = await dao.session.scalar(
        select(models.FileInfo.id).where(models.FileInfo.guid == guid)
    )
    assert file_id is not None
    return file_id


@pytest.mark.asyncio
async def test_upsert_game_fills_level_and_game_files(
    author: dto.Player,
    complex_scn: RawGameScenario,
    dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
):
    game = await upsert_game(complex_scn, author, dao.game_upserter, retort, file_gateway)
    file_id = await _file_id_by_guid(dao, GUID)

    first, second = game.levels[0], game.levels[1]
    # only the first level references the file
    assert await _level_file_ids(dao, first.db_id) == {file_id}
    assert await _level_file_ids(dao, second.db_id) == set()
    # the file is registered as usable in the game
    assert await _game_file_ids(dao, game.id) == {file_id}


@pytest.mark.asyncio
async def test_removing_file_syncs_level_files_but_keeps_game_files(
    author: dto.Player,
    complex_scn: RawGameScenario,
    dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
):
    game = await upsert_game(complex_scn, author, dao.game_upserter, retort, file_gateway)
    file_id = await _file_id_by_guid(dao, GUID)
    first = game.levels[0]
    assert await _level_file_ids(dao, first.db_id) == {file_id}

    stripped = deepcopy(complex_scn.scn)
    _strip_files(stripped["levels"][0])
    # the file is still declared in the "files" section (kept uploaded for the game),
    # it is just no longer referenced by any level hint.
    await upsert_game(
        RawGameScenario(scn=stripped, files={GUID: BytesIO(b"123")}),
        author,
        dao.game_upserter,
        retort,
        file_gateway,
    )

    # the level no longer references the file, so level_files is synced empty ...
    assert await _level_file_ids(dao, first.db_id) == set()
    # ... but the game keeps it as a usable file (never removed)
    assert await _game_file_ids(dao, game.id) == {file_id}


def _strip_files(level: dict) -> None:
    level["time_hints"] = [
        th for th in level["time_hints"] if not any("file_guid" in h for h in th["hint"])
    ]
    level["conditions"] = [
        c
        for c in level["conditions"]
        if not any("file_guid" in h for h in c.get("effects", {}).get("hints", []))
    ]
