import pytest

from db.dao.holder import HolderDao
from tests.fixtures.user_constants import create_tg_user
from tgbot.middlewares.data_load_middleware import save_user, save_player


@pytest.mark.asyncio
async def test_save_player(dao: HolderDao):
    data = dict(event_from_user=create_tg_user())
    saved_user = await save_user(data, dao)
    actual_player = await save_player(saved_user, dao)
    assert await dao.user.count() == 1
    assert await dao.player.count() == 1
    assert saved_user.db_id == actual_player.user.db_id
    assert actual_player.id is not None


@pytest.mark.asyncio
async def test_upsert_player(dao: HolderDao):
    await test_save_player(dao)

    data = dict(event_from_user=create_tg_user())
    saved_user = await save_user(data, dao)

    saved_player_id = (await dao.player._get_all())[0].id
    expected_player = await dao.player.get_by_id(saved_player_id)

    actual_player = await save_player(saved_user, dao)
    assert expected_player == actual_player
