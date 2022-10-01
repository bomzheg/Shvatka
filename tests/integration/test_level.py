import pytest
from dataclass_factory import Factory

from db.dao.holder import HolderDao
from shvatka.models.dto.scn.level import LevelScenario
from shvatka.services.level import upsert_raw_level
from shvatka.services.player import upsert_player
from shvatka.services.user import upsert_user
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_simple_level(simple_scn: dict, dao: HolderDao, dcf: Factory):
    author = await upsert_player(await upsert_user(create_dto_harry(), dao.user), dao.player)
    await dao.player.promote(author, author)
    await dao.commit()
    author.can_be_author = True
    lvl = await upsert_raw_level(simple_scn["levels"][0], author, dcf, dao.level)

    assert lvl.db_id is not None
    assert await dao.level.count() == 1

    assert isinstance(lvl.scenario, LevelScenario)
    assert lvl.scenario.id == lvl.name_id
    assert lvl.author == author
    assert lvl.game_id is None
    assert lvl.number_in_game is None

    assert lvl.scenario.keys == {"SHOOT"}
