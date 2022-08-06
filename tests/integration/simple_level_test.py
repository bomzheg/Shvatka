import pytest
from dataclass_factory import Factory

from app.dao.holder import HolderDao
from app.models.db import Level
from app.models.dto.scn.level import LeveScenario
from app.services.player import upsert_player
from app.services.scenario.game_ops import load_game
from app.services.user import upsert_user
from tests.fixtures.user_constants import create_dto_harry


@pytest.mark.asyncio
async def test_simple_level(simple_scn: dict, dao: HolderDao, dcf: Factory):
    author = await upsert_player(await upsert_user(create_dto_harry(), dao.user), dao.player)
    scn = load_game(simple_scn, dcf)
    level_scn = scn.levels[0]
    lvl = Level(
        name_id=level_scn.id,
        scenario=level_scn,
        author_id=author.id
    )
    dao.level.save(lvl)
    await dao.level.flush(lvl)
    await dao.level.commit()
    assert lvl.id is not None
    assert await dao.level.count()
    actual = await dao.level.get_by_id(lvl.id)
    assert level_scn.time_hints == actual.scenario.time_hints
    assert isinstance(actual.scenario, LeveScenario)
