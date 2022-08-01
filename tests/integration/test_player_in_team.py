import pytest

from app.dao.holder import HolderDao
from app.services.chat import upsert_chat
from app.services.player import upsert_player, add_player_in_team, get_my_team
from app.services.team import create_team
from app.services.user import upsert_user
from app.utils.exceptions import UserAlreadyInTeam
from tests.fixtures.chat_constants import create_dto_chat, create_another_chat
from tests.fixtures.user_constants import create_dto_harry, create_dto_hermione, create_dto_ron


@pytest.mark.asyncio
async def test_add_player_to_team(dao: HolderDao):
    captain = await upsert_player(await upsert_user(create_dto_harry(), dao.user), dao.player)

    team = await create_team(await upsert_chat(create_dto_chat(), dao.chat), captain, dao)
    assert 1 == await dao.player_in_team.count()
    assert team == await get_my_team(captain, dao.player_in_team)

    player = await upsert_player(await upsert_user(create_dto_hermione(), dao.user), dao.player)
    await add_player_in_team(player, team, dao.player_in_team)
    assert team == await get_my_team(player, dao.player_in_team)
    assert 2 == await dao.player_in_team.count()

    with pytest.raises(UserAlreadyInTeam):
        await add_player_in_team(captain, team, dao.player_in_team)

    with pytest.raises(UserAlreadyInTeam):
        await add_player_in_team(player, team, dao.player_in_team)

    with pytest.raises(UserAlreadyInTeam):
        await create_team(await upsert_chat(create_another_chat(), dao.chat), player, dao)

    assert 2 == await dao.player_in_team.count()

    player_ron = await upsert_player(await upsert_user(create_dto_ron(), dao.user), dao.player)
    rons_team = await create_team(await upsert_chat(create_another_chat(), dao.chat), player_ron, dao)

    assert 3 == await dao.player_in_team.count()

    with pytest.raises(UserAlreadyInTeam):
        await add_player_in_team(captain, rons_team, dao.player_in_team)

    with pytest.raises(UserAlreadyInTeam):
        await add_player_in_team(player, rons_team, dao.player_in_team)

    assert 3 == await dao.player_in_team.count()
