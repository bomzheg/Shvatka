import pytest

from app.dao.holder import HolderDao
from app.middlewares.data_load_middleware import save_user
from tests.fixtures.user_constants import create_tg_user, create_dto_user
from tests.utils.user import assert_user


@pytest.mark.asyncio
async def test_save_user(dao: HolderDao):
    await dao.user.delete_all()

    data = dict(event_from_user=create_tg_user())
    actual = await save_user(data, dao)
    expected = create_dto_user()
    assert_user(expected, actual)
    assert actual.db_id is not None
    assert await dao.user.count() == 1


@pytest.mark.asyncio
async def test_upsert_user(dao: HolderDao):
    await dao.user.delete_all()

    old_tg_user = create_tg_user(username="tom_riddle_friend")
    data = dict(event_from_user=old_tg_user)
    old = await save_user(data, dao)
    expected_old = create_dto_user()
    expected_old.username = "tom_riddle_friend"
    assert_user(expected_old, old)

    data = dict(event_from_user=create_tg_user())
    actual = await save_user(data, dao)

    expected = create_dto_user()
    assert_user(expected, actual)
    assert old.db_id == actual.db_id
    assert await dao.user.count() == 1
