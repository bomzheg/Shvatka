import pytest

from app.dao.holder import HolderDao
from app.middlewares.data_load_middleware import save_chat
from app.services.chat import update_chat_id, upsert_chat
from tests.fixtures.chat_constants import create_tg_chat, create_db_chat, create_dto_chat, NEW_CHAT_ID
from tests.utils.chat import assert_dto_chat, assert_db_chat


@pytest.mark.asyncio
async def test_save_chat(dao: HolderDao):
    await dao.chat.delete_all()

    data = dict(event_chat=create_tg_chat())
    actual = await save_chat(data, dao)
    expected = create_dto_chat()
    assert_dto_chat(expected, actual)
    assert actual.db_id is not None
    assert await dao.chat.count() == 1


@pytest.mark.asyncio
async def test_migrate_to_supergroup(dao: HolderDao):
    await dao.chat.delete_all()

    old_chat = create_dto_chat()
    await upsert_chat(old_chat, dao.chat)
    old_count = await dao.chat.count()

    await update_chat_id(old_chat, NEW_CHAT_ID, dao.chat)

    expected = create_db_chat()
    expected.tg_id = NEW_CHAT_ID

    actual = await dao.chat.get_by_tg_id(NEW_CHAT_ID)

    assert_db_chat(expected, actual)
    assert actual.id is not None
    assert await dao.chat.count() == old_count


@pytest.mark.asyncio
async def test_upsert_chat(dao: HolderDao):
    await dao.chat.delete_all()

    data = dict(event_chat=create_tg_chat(username="extra_chat"))
    old_chat = await save_chat(data, dao)
    old_count = await dao.chat.count()
    assert old_chat.username == "extra_chat"

    data = dict(event_chat=create_tg_chat())
    actual = await save_chat(data, dao)
    expected = create_dto_chat()
    assert_dto_chat(expected, actual)

    assert_dto_chat(expected, actual)
    assert old_chat.db_id == actual.db_id
    assert await dao.chat.count() == old_count
