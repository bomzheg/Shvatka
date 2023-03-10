import pytest

from shvatka.core.models import dto
from shvatka.core.services.player import get_full_team_player
from shvatka.core.services.team import rename_team, change_team_desc, get_teams
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.chat_constants import GRYFFINDOR_CHAT_DTO


@pytest.mark.asyncio
async def test_rename(
    gryffindor: dto.Team, harry: dto.Player, dao: HolderDao, check_dao: HolderDao
):
    assert GRYFFINDOR_CHAT_DTO.title == gryffindor.name
    team_player = await get_full_team_player(player=harry, team=gryffindor, dao=dao.team_player)
    await rename_team(gryffindor, team_player, "Гриффиндор", dao.team)
    actual_team = await check_dao.team.get_by_id(id_=gryffindor.id)
    assert "Гриффиндор" == actual_team.name


@pytest.mark.asyncio
async def test_change_desc(
    gryffindor: dto.Team, harry: dto.Player, dao: HolderDao, check_dao: HolderDao
):
    assert GRYFFINDOR_CHAT_DTO.description == gryffindor.description
    team_player = await get_full_team_player(player=harry, team=gryffindor, dao=dao.team_player)
    await change_team_desc(gryffindor, team_player, "slytherin must die!", dao.team)
    actual_team = await check_dao.team.get_by_id(id_=gryffindor.id)
    assert "slytherin must die!" == actual_team.description


@pytest.mark.asyncio
async def test_get_all_teams_no_team(dao: HolderDao):
    teams = await get_teams(dao.team)
    assert 0 == len(teams)


@pytest.mark.asyncio
async def test_get_all_teams_one_team(gryffindor: dto.Team, dao: HolderDao):
    teams = await get_teams(dao.team)
    assert 1 == len(teams)
    assert gryffindor.id == teams[0].id


@pytest.mark.asyncio
async def test_get_all_teams_two_teams(gryffindor: dto.Team, slytherin: dto.Team, dao: HolderDao):
    teams = await get_teams(dao.team)
    assert 2 == len(teams)
    assert {gryffindor.id, slytherin.id} == {teams[0].id, teams[1].id}
