import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.holder import HolderDao
from app.middlewares.data_load_middleware import save_user
from app.models import dto
from tests.fixtures.user_constants import create_tg_user, create_db_user
from tests.utils.user import assert_user


@pytest.mark.asyncio
async def test_save_user(session: AsyncSession):
    dao = HolderDao(session)
    await dao.user.delete_all()

    data = dict(event_from_user=create_tg_user())
    actual = await save_user(data, dao)
    expected = dto.User.from_db(create_db_user())
    assert_user(expected, actual)
    assert actual.db_id is not None
    assert await dao.user.count() == 1
