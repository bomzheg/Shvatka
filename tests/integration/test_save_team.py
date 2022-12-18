import pytest

from infrastructure.db.dao.holder import HolderDao
from shvatka.services.chat import upsert_chat
from shvatka.services.player import upsert_player
from shvatka.services.team import create_team, get_by_chat
from shvatka.services.user import upsert_user
from tests.fixtures.chat_constants import create_gryffindor_dto_chat
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_save_team(dao: HolderDao):
    chat = await upsert_chat(create_gryffindor_dto_chat(), dao.chat)
    user = await upsert_user(create_dto_harry(), dao.user)
    player = await upsert_player(user, dao.player)
    team = await create_team(chat, player, dao.team_creator)
    assert team.id is not None
    assert team.name == chat.name


@pytest.mark.asyncio
async def test_get_team(dao: HolderDao):
    chat = await upsert_chat(create_gryffindor_dto_chat(), dao.chat)
    assert await get_by_chat(chat, dao.team) is None

    await test_save_team(dao)
    chat = (await dao.chat._get_all())[0]

    team = await get_by_chat(chat.to_dto(), dao.team)
    assert team.id is not None
    assert team.name == chat.title
