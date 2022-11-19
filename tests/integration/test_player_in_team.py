import pytest

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import join_team, get_my_team, get_my_role
from shvatka.utils.defaults_constants import DEFAULT_ROLE, CAPTAIN_ROLE
from shvatka.utils.exceptions import PlayerAlreadyInTeam, PermissionsError
from tests.fixtures.team import create_second_team


@pytest.mark.asyncio
async def test_add_player_to_team(
    harry: dto.Player, hermione: dto.Player, draco: dto.Player, gryffindor: dto.Team, dao: HolderDao,
):
    assert 1 == await dao.team_player.count()
    assert gryffindor == await get_my_team(harry, dao.team_player)
    assert CAPTAIN_ROLE == await get_my_role(harry, dao.team_player)

    await join_team(hermione, gryffindor, harry, dao.team_player)
    assert gryffindor == await get_my_team(hermione, dao.team_player)
    assert 2 == await dao.team_player.count()
    assert DEFAULT_ROLE == await get_my_role(hermione, dao.team_player)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(harry, gryffindor, harry, dao.team_player)

    with pytest.raises(PermissionsError):
        await join_team(draco, gryffindor, hermione, dao.team_player)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(hermione, gryffindor, harry, dao.team_player)

    with pytest.raises(PlayerAlreadyInTeam):
        await create_second_team(hermione, dao)

    assert 2 == await dao.team_player.count()

    slytherin = await create_second_team(draco, dao)

    assert 3 == await dao.team_player.count()
    assert CAPTAIN_ROLE == await get_my_role(draco, dao.team_player)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(harry, slytherin, draco, dao.team_player)

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(hermione, slytherin, draco, dao.team_player)

    assert 3 == await dao.team_player.count()
