import pytest

from app.dao.holder import HolderDao
from app.services.player import join_team, get_my_team, get_my_role
from app.utils.defaults_constants import DEFAULT_ROLE, CAPTAIN_ROLE
from app.utils.exceptions import PlayerAlreadyInTeam
from tests.utils.player import create_hermi_player, create_harry_player, create_ron_player
from tests.utils.team import create_first_team, create_second_team


@pytest.mark.asyncio
async def test_add_player_to_team(dao: HolderDao):
    captain = await create_harry_player(dao)
    team = await create_first_team(captain, dao)

    assert 1 == await dao.player_in_team.count()
    assert team == await get_my_team(captain, dao.player_in_team)
    assert CAPTAIN_ROLE == await get_my_role(captain, dao.player_in_team)

    player = await create_hermi_player(dao)
    await join_team(player, team, dao.player_in_team)
    assert team == await get_my_team(player, dao.player_in_team)
    assert 2 == await dao.player_in_team.count()
    assert DEFAULT_ROLE == await get_my_role(player, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(captain, team, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(player, team, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await create_second_team(player, dao)

    assert 2 == await dao.player_in_team.count()

    player_ron = await create_ron_player(dao)
    rons_team = await create_second_team(player_ron, dao)

    assert 3 == await dao.player_in_team.count()
    assert CAPTAIN_ROLE == await get_my_role(player_ron, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(captain, rons_team, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(player, rons_team, dao.player_in_team)

    assert 3 == await dao.player_in_team.count()
