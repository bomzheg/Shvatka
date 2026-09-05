from copy import deepcopy

import pytest
from adaptix import Retort

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.services.game import upsert_game
from shvatka.core.utils.exceptions import FilesCantBeSentToTg
from shvatka.infrastructure.db.dao.complex.game import GameUpserterImpl
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID
from tests.mocks.file_gateway import FakeTelegram


def _scn_with_file_not_yet_in_tg(complex_scn: RawGameScenario) -> RawGameScenario:
    scn = deepcopy(complex_scn.scn)
    (file_meta,) = (f for f in scn["files"] if f["guid"] == GUID)
    del file_meta["file_id"]
    return RawGameScenario(scn=scn, files=complex_scn.files)


@pytest.mark.asyncio
async def test_upsert_game_saves_nothing_when_telegram_refuses_a_file(
    author: dto.Player,
    complex_scn: RawGameScenario,
    dao: HolderDao,
    check_dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
    telegram: FakeTelegram,
):
    telegram.refuse = True

    with pytest.raises(FilesCantBeSentToTg) as exc_info:
        await upsert_game(
            _scn_with_file_not_yet_in_tg(complex_scn),
            author,
            GameUpserterImpl(dao),
            retort,
            file_gateway,
        )

    assert {e.guid for e in exc_info.value.errors} == {GUID}
    assert telegram.sent == [GUID]
    assert await check_dao.game.count() == 0


@pytest.mark.asyncio
async def test_upsert_game_saves_the_files_telegram_took(
    author: dto.Player,
    complex_scn: RawGameScenario,
    dao: HolderDao,
    check_dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
    telegram: FakeTelegram,
):
    game = await upsert_game(
        _scn_with_file_not_yet_in_tg(complex_scn),
        author,
        GameUpserterImpl(dao),
        retort,
        file_gateway,
    )

    assert telegram.sent == [GUID]
    assert await check_dao.game.count() == 1
    assert game.levels
    meta = await check_dao.file_info.get_by_guid(GUID)
    # telegram took it, so the game can send it by file_id from now on
    assert meta.file_id is not None
