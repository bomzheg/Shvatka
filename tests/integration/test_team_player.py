import pytest

from db.dao.holder import HolderDao
from shvatka.models import dto, enums
from shvatka.services.player import join_team, get_my_team, get_my_role, flip_permission, get_full_team_player
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


@pytest.mark.asyncio
async def test_flip_permission(
    harry: dto.Player, hermione: dto.Player, gryffindor: dto.Team,
    dao: HolderDao, check_dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player)
    permission = enums.TeamPlayerPermission.can_change_team_name
    harry_team_player = await get_full_team_player(harry, gryffindor, dao.team_player)
    hermione_team_player = await get_full_team_player(hermione, gryffindor, dao.team_player)
    assert not hermione_team_player.can_change_team_name
    await flip_permission(harry_team_player, hermione_team_player, permission, dao.team_player)

    actual = await get_full_team_player(hermione, gryffindor, check_dao.team_player)
    assert actual.can_change_team_name
