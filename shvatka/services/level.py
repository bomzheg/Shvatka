from dataclass_factory import Factory

from shvatka.dal.level import LevelUpserter, MyLevelsGetter
from shvatka.models import dto
from shvatka.models.dto.scn.level import LevelScenario
from shvatka.services.player import check_allow_be_author
from shvatka.services.scenario.level_ops import load_level


async def upsert_raw_level(
    level_data: dict, author: dto.Player, dcf: Factory, dao: LevelUpserter
) -> dto.Level:
    check_allow_be_author(author)
    scn = load_level(level_data, dcf)
    return await upsert_level(author, scn, dao)


async def upsert_level(author: dto.Player, scn: LevelScenario, dao: LevelUpserter):
    check_allow_be_author(author)
    result = await dao.upsert(author, scn)
    await dao.commit()
    return result


async def get_all_my_levels(author: dto.Player, dao: MyLevelsGetter) -> list[dto.Level]:
    return await dao.get_all_my(author)
