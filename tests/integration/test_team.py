import pytest

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import get_team_player
from shvatka.services.team import rename_team
from tests.fixtures.chat_constants import GRYFFINDOR_CHAT_DTO


@pytest.mark.asyncio
async def test_rename(gryffindor: dto.Team, harry: dto.Player, dao: HolderDao, check_dao: HolderDao):
    assert GRYFFINDOR_CHAT_DTO.title == gryffindor.name
    team_player = await get_team_player(player=harry, team=gryffindor, dao=dao.team_player)
    await rename_team(gryffindor, team_player, "Гриффиндор", dao.team)
    actual_team = await check_dao.team.get_by_id(id_=gryffindor.id)
    assert "Гриффиндор" == actual_team.name
