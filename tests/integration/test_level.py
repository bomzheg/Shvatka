import pytest
from adaptix import Retort

from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.models.dto.scn.level import LevelScenario
from shvatka.core.services.level import upsert_raw_level
from shvatka.core.services.player import upsert_player
from shvatka.core.services.user import upsert_user
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_simple_level(simple_scn: RawGameScenario, dao: HolderDao, retort: Retort):
    author = await upsert_player(await upsert_user(create_dto_harry(), dao.user), dao.player)
    await dao.player.promote(author, author)
    await dao.commit()
    author.can_be_author = True
    lvl = await upsert_raw_level(simple_scn.scn["levels"][0], author, retort, dao.level)

    assert lvl.db_id is not None
    assert await dao.level.count() == 1

    assert isinstance(lvl.scenario, LevelScenario)
    assert lvl.scenario.id == lvl.name_id
    assert lvl.author == author
    assert lvl.game_id is None
    assert lvl.number_in_game is None

    assert lvl.scenario.get_keys() == {"SH123", "SH321"}
