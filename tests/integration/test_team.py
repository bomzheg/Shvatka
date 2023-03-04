import pytest

from src.infrastructure.db.dao.holder import HolderDao
from src.shvatka.models import dto
from src.shvatka.services.player import get_full_team_player
from src.shvatka.services.team import rename_team, change_team_desc
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
