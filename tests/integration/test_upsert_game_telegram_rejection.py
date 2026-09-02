import typing
from unittest.mock import MagicMock

import pytest
from adaptix import Retort
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendDocument

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.services.game import upsert_game
from shvatka.core.utils.exceptions import FilesCantBeSentToTg
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.scn_fixtures import GUID


@pytest.mark.asyncio
async def test_upsert_game_reports_every_file_telegram_refuses(
    author: dto.Player,
    complex_scn: RawGameScenario,
    dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
    bot_session: BaseSession,
):
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [TelegramAPIError(message="file too large", method=SendDocument)]

    with pytest.raises(FilesCantBeSentToTg) as exc_info:
        await upsert_game(complex_scn, author, dao.game_upserter, retort, file_gateway)

    assert {e.guid for e in exc_info.value.errors} == {GUID}
    assert await dao.game.count() == 0


@pytest.mark.asyncio
async def test_upsert_game_force_saves_the_file_telegram_refused(
    author: dto.Player,
    complex_scn: RawGameScenario,
    dao: HolderDao,
    check_dao: HolderDao,
    retort: Retort,
    file_gateway: FileGateway,
    bot_session: BaseSession,
):
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [TelegramAPIError(message="file too large", method=SendDocument)]

    game = await upsert_game(
        complex_scn, author, dao.game_upserter, retort, file_gateway, force=True
    )

    assert await check_dao.game.count() == 1
    assert game.levels
    meta = await check_dao.file_info.get_by_guid(GUID)
    # telegram refused it, so it was stored without a file_id — it will be sent
    # by content the first time it is shown in a game
    assert meta.file_id is None
