import pytest

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import join_team, get_my_team, get_my_role
from shvatka.utils.defaults_constants import DEFAULT_ROLE, CAPTAIN_ROLE
from shvatka.utils.exceptions import PlayerAlreadyInTeam
from tests.fixtures.team import create_second_team


@pytest.mark.asyncio
async def test_add_player_to_team(
    harry: dto.Player, hermione: dto.Player, ron: dto.Player, gryffindor: dto.Team, dao: HolderDao,
):
    assert 1 == await dao.player_in_team.count()
    assert gryffindor == await get_my_team(harry, dao.player_in_team)
    assert CAPTAIN_ROLE == await get_my_role(harry, dao.player_in_team)

    await join_team(hermione, gryffindor, dao.player_in_team)
    assert gryffindor == await get_my_team(hermione, dao.player_in_team)
    assert 2 == await dao.player_in_team.count()
    assert DEFAULT_ROLE == await get_my_role(hermione, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(harry, gryffindor, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(hermione, gryffindor, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await create_second_team(hermione, dao)

    assert 2 == await dao.player_in_team.count()

    rons_team = await create_second_team(ron, dao)

    assert 3 == await dao.player_in_team.count()
    assert CAPTAIN_ROLE == await get_my_role(ron, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(harry, rons_team, dao.player_in_team)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(hermione, rons_team, dao.player_in_team)

    assert 3 == await dao.player_in_team.count()
