import pytest

from shvatka.core.services.chat import upsert_chat
from shvatka.core.services.player import upsert_player
from shvatka.core.services.team import create_team, get_by_chat
from shvatka.core.services.user import upsert_user
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.chat_constants import create_gryffindor_dto_chat
from tests.fixtures.player import promote
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_save_team(dao: HolderDao, game_log: GameLogWriter):
    chat = await upsert_chat(create_gryffindor_dto_chat(), dao.chat)
    user = await upsert_user(create_dto_harry(), dao.user)
    player = await upsert_player(user, dao.player)
    await promote(player, dao)
    team = await create_team(chat, player, dao.team_creator, game_log)
    assert team.id is not None
    assert team.name == chat.name


@pytest.mark.asyncio
async def test_get_team(dao: HolderDao, game_log: GameLogWriter):
    chat = await upsert_chat(create_gryffindor_dto_chat(), dao.chat)
    assert await get_by_chat(chat, dao.team) is None

    await test_save_team(dao, game_log)

    team = await get_by_chat(chat, dao.team)
    assert team is not None
    assert team.id is not None
    assert team.name == chat.title
