from dataclass_factory import Factory

from app.dao import LevelDao
from app.models import dto
from app.services.scenario.level_ops import load_level


async def upsert_level(
    level_data: dict, author: dto.Player, dcf: Factory, dao: LevelDao
) -> dto.Level:
    scn = load_level(level_data, dcf)
    await dao.commit()
    return await dao.upsert(author, scn)
