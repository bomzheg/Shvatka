from copy import deepcopy
from io import BytesIO

import pytest
from adaptix import Retort

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.services.game import upsert_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID


@pytest.mark.asyncio
async def test_upsert_game_fills_level_and_game_files(
    author: dto.Player,
    complex_scn: RawGameScenario,
    dao: HolderDao,
    check_dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
):
    game = await upsert_game(complex_scn, author, dao.game_upserter, retort, file_gateway)
    (file_id,) = await check_dao.file_info.get_ids_by_guids([GUID])

    first, second = game.levels[0], game.levels[1]
    # only the first level references the file
    assert await check_dao.file_link.get_level_file_ids(first.db_id) == {file_id}
    assert await check_dao.file_link.get_level_file_ids(second.db_id) == set()
    # the file is registered as usable in the game
    assert await check_dao.file_link.get_game_file_ids(game.id) == {file_id}


@pytest.mark.asyncio
async def test_removing_file_syncs_level_files_but_keeps_game_files(
    author: dto.Player,
    complex_scn: RawGameScenario,
    dao: HolderDao,
    check_dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
):
    game = await upsert_game(complex_scn, author, dao.game_upserter, retort, file_gateway)
    (file_id,) = await check_dao.file_info.get_ids_by_guids([GUID])
    first = game.levels[0]
    assert await check_dao.file_link.get_level_file_ids(first.db_id) == {file_id}

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
    assert await check_dao.file_link.get_level_file_ids(first.db_id) == set()
    # ... but the game keeps it as a usable file (never removed)
    assert await check_dao.file_link.get_game_file_ids(game.id) == {file_id}


def _strip_files(level: dict) -> None:
    level["time_hints"] = [
        th for th in level["time_hints"] if not any("file_guid" in h for h in th["hint"])
    ]
    level["conditions"] = [
        c
        for c in level["conditions"]
        if not any("file_guid" in h for h in c.get("effects", {}).get("hints", []))
    ]
