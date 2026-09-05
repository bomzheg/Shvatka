import pytest

from shvatka.core.models import dto, enums
from shvatka.core.players.player import (
    flip_permission,
    get_full_team_player,
    get_my_role,
    get_my_team,
    join_team,
    leave,
)
from shvatka.core.utils import exceptions
from shvatka.core.utils.defaults_constants import CAPTAIN_ROLE, DEFAULT_ROLE
from shvatka.core.utils.exceptions import CantBeAuthor, PermissionsError, PlayerAlreadyInTeam
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.complex.team import TeamLeaverImpl
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.player import promote
from tests.fixtures.team import create_second_team
from tests.mocks.team_notifier import TeamNotifierMock


@pytest.mark.asyncio
async def test_add_player_to_team(
    harry: dto.Player,
    hermione: dto.Player,
    draco: dto.Player,
    gryffindor: dto.Team,
    dao: HolderDao,
    game_log: GameLogWriter,
):
    assert await dao.team_player.count() == 1
    assert gryffindor == await get_my_team(harry, dao.team_player)
    assert await get_my_role(harry, dao.team_player) == CAPTAIN_ROLE

    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    assert gryffindor == await get_my_team(hermione, dao.team_player)
    assert await dao.team_player.count() == 2
    assert await get_my_role(hermione, dao.team_player) == DEFAULT_ROLE

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(harry, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())

    with pytest.raises(PermissionsError):
        await join_team(draco, gryffindor, hermione, dao.team_player, notifier=TeamNotifierMock())

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())

    with pytest.raises(CantBeAuthor):
        await create_second_team(hermione, dao, game_log)

    await promote(hermione, dao)
    with pytest.raises(PlayerAlreadyInTeam):
        await create_second_team(hermione, dao, game_log)

    assert await dao.team_player.count() == 2

    slytherin = await create_second_team(draco, dao, game_log)

    assert await dao.team_player.count() == 3
    assert await get_my_role(draco, dao.team_player) == CAPTAIN_ROLE

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(harry, slytherin, draco, dao.team_player, notifier=TeamNotifierMock())

    with pytest.raises(PlayerAlreadyInTeam):
        await join_team(hermione, slytherin, draco, dao.team_player, notifier=TeamNotifierMock())

    assert await dao.team_player.count() == 3


@pytest.mark.asyncio
async def test_restore_player_to_team(
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    dao: HolderDao,
    game_log: GameLogWriter,
):
    players = await dao.team_player.get_players(gryffindor)
    assert len(players) == 1
    assert players[0].player_id == harry.id
    assert await dao.team_player.count() == 1
    assert await get_my_role(harry, dao.team_player) == CAPTAIN_ROLE

    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())

    assert gryffindor == await get_my_team(hermione, dao.team_player)
    assert await dao.team_player.count() == 2
    assert await get_my_role(hermione, dao.team_player) == DEFAULT_ROLE

    await leave(hermione, harry, TeamLeaverImpl(dao), notifier=TeamNotifierMock())

    players = await dao.team_player.get_players(gryffindor)
    assert len(players) == 1
    with pytest.raises(exceptions.PlayerRestoredInTeam):
        await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())

    assert gryffindor == await get_my_team(hermione, dao.team_player)
    assert await dao.team_player.count() == 2
    assert await get_my_role(hermione, dao.team_player) == DEFAULT_ROLE


@pytest.mark.asyncio
async def test_no_restore_player_to_team_just_add(
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    draco: dto.Player,
    slytherin: dto.Team,
    dao: HolderDao,
    game_log: GameLogWriter,
):
    players = await dao.team_player.get_players(gryffindor)
    assert len(players) == 1
    assert players[0].player_id == harry.id

    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())

    assert gryffindor == await get_my_team(hermione, dao.team_player)
    assert await get_my_role(hermione, dao.team_player) == DEFAULT_ROLE

    await leave(hermione, hermione, TeamLeaverImpl(dao), notifier=TeamNotifierMock())

    await join_team(hermione, slytherin, draco, dao.team_player, notifier=TeamNotifierMock())
    await leave(hermione, hermione, TeamLeaverImpl(dao), notifier=TeamNotifierMock())

    players = await dao.team_player.get_players(gryffindor)
    assert len(players) == 1
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())

    assert gryffindor == await get_my_team(hermione, dao.team_player)
    assert await get_my_role(hermione, dao.team_player) == DEFAULT_ROLE


@pytest.mark.asyncio
async def test_flip_permission(
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    dao: HolderDao,
    check_dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    permission = enums.TeamPlayerPermission.can_change_team_name
    harry_team_player = await get_full_team_player(harry, gryffindor, dao.team_player)
    hermione_team_player = await get_full_team_player(hermione, gryffindor, dao.team_player)
    assert not hermione_team_player.can_change_team_name
    await flip_permission(harry_team_player, hermione_team_player, permission, dao.team_player)

    actual = await get_full_team_player(hermione, gryffindor, check_dao.team_player)
    assert actual.can_change_team_name
