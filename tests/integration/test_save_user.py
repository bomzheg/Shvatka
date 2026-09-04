from typing import cast

import pytest

from shvatka.infrastructure.db import models
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.services.identity import save_user
from shvatka.tgbot.utils.data import SHMiddlewareData
from tests.fixtures.user_constants import HARRY_OLD_USERNAME, create_dto_harry, create_tg_user
from tests.utils.user import assert_user


@pytest.mark.asyncio
async def test_save_user(dao: HolderDao):
    data = cast(SHMiddlewareData, {"event_from_user": create_tg_user()})
    actual = await save_user(data, dao)
    expected = create_dto_harry()
    assert_user(expected, actual)
    assert actual.db_id is not None
    assert await dao.user.count() == 1


@pytest.mark.asyncio
async def test_upsert_user(dao: HolderDao):
    old_tg_user = create_tg_user(username=HARRY_OLD_USERNAME)
    data = cast(SHMiddlewareData, {"event_from_user": old_tg_user})
    old = await save_user(data, dao)
    expected_old = create_dto_harry()
    expected_old.username = HARRY_OLD_USERNAME
    assert_user(expected_old, old)

    data = cast(SHMiddlewareData, {"event_from_user": create_tg_user()})
    actual = await save_user(data, dao)

    expected = create_dto_harry()
    assert_user(expected, actual)
    assert old.db_id == actual.db_id
    assert await dao.user.count() == 1


@pytest.mark.asyncio
async def test_upsert_user_refreshes_already_loaded_user(dao: HolderDao):
    old = await dao.user.upsert_user(create_dto_harry())
    await dao.commit()
    # keep the mapped instance alive, so it can't leave the identity map
    loaded = await dao.session.get(models.User, old.db_id)
    assert loaded is not None

    renamed = create_dto_harry()
    renamed.first_name = "Гарри"
    renamed.last_name = "Поттер"
    actual = await dao.user.upsert_user(renamed)
    await dao.commit()

    assert_user(renamed, actual)
    assert loaded.first_name == "Гарри"
    assert loaded.last_name == "Поттер"
