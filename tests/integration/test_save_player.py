from typing import cast

import pytest

from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.services.identity import save_user, save_player
from shvatka.tgbot.utils.data import SHMiddlewareData
from tests.fixtures.user_constants import create_tg_user


@pytest.mark.asyncio
async def test_save_player(dao: HolderDao):
    data = cast(SHMiddlewareData, {"event_from_user": create_tg_user()})
    saved_user = await save_user(data, dao)
    actual_player = await save_player(saved_user, dao)
    assert await dao.user.count() == 1
    assert await dao.player.count() == 1
    assert saved_user.db_id == actual_player._user.db_id
    assert actual_player.id is not None


@pytest.mark.asyncio
async def test_upsert_player(dao: HolderDao):
    await test_save_player(dao)

    data = cast(SHMiddlewareData, {"event_from_user": create_tg_user()})
    saved_user = await save_user(data, dao)

    saved_player_id = (await dao.player._get_all())[0].id
    expected_player = await dao.player.get_by_id(saved_player_id)

    actual_player = await save_player(saved_user, dao)
    assert expected_player == actual_player
