import pytest

from app.dao.holder import HolderDao
from app.models import dto
from app.services.chat import upsert_chat
from app.services.player import upsert_player
from app.services.team import create_team, get_by_chat
from app.services.user import upsert_user
from tests.fixtures.chat_constants import create_dto_chat
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_save_team(dao: HolderDao):
    chat = await upsert_chat(create_dto_chat(), dao.chat)
    user = await upsert_user(create_dto_harry(), dao.user)
    player = await upsert_player(user, dao.player)
    team = await create_team(chat, player, dao)
    assert team.id is not None
    assert team.name == chat.name


@pytest.mark.asyncio
async def test_get_team(dao: HolderDao):
    chat = await upsert_chat(create_dto_chat(), dao.chat)
    assert await get_by_chat(chat, dao.team) is None

    await test_save_team(dao)
    chat = (await dao.chat.get_all())[0][0]

    team = await get_by_chat(dto.Chat.from_db(chat), dao.team)
    assert team.id is not None
    assert team.name == chat.title
