import pytest

from shvatka.core.models import dto
from shvatka.core.players.player import get_full_team_player
from shvatka.core.services.game import complete_game
from shvatka.core.services.team import change_team_desc, get_played_games, get_teams, rename_team
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
    assert actual_team.name == "Гриффиндор"


@pytest.mark.asyncio
async def test_change_desc(
    gryffindor: dto.Team, harry: dto.Player, dao: HolderDao, check_dao: HolderDao
):
    assert GRYFFINDOR_CHAT_DTO.description == gryffindor.description
    team_player = await get_full_team_player(player=harry, team=gryffindor, dao=dao.team_player)
    await change_team_desc(gryffindor, team_player, "slytherin must die!", dao.team)
    actual_team = await check_dao.team.get_by_id(id_=gryffindor.id)
    assert actual_team.description == "slytherin must die!"


@pytest.mark.asyncio
async def test_get_all_teams_no_team(dao: HolderDao):
    teams = await get_teams(dao.team)
    assert len(teams) == 0


@pytest.mark.asyncio
async def test_get_all_teams_one_team(gryffindor: dto.Team, dao: HolderDao):
    teams = await get_teams(dao.team)
    assert len(teams) == 1
    assert gryffindor.id == teams[0].id


@pytest.mark.asyncio
async def test_get_all_teams_two_teams(gryffindor: dto.Team, slytherin: dto.Team, dao: HolderDao):
    teams = await get_teams(dao.team)
    assert len(teams) == 2
    assert {gryffindor.id, slytherin.id} == {teams[0].id, teams[1].id}


@pytest.mark.asyncio
async def test_get_played(gryffindor: dto.Team, finished_game: dto.Game, dao: HolderDao):
    await complete_game(finished_game, dao.game)
    games = await get_played_games(gryffindor, dao.team)
    assert len(games) == 1
    assert finished_game.id == games[0].id
