from dataclass_factory import Factory

from shvatka.dal.level import LevelUpserter, MyLevelsGetter, LevelByIdGetter
from shvatka.models import dto
from shvatka.models.dto.scn.level import LevelScenario
from shvatka.services.player import check_allow_be_author
from shvatka.services.scenario.level_ops import load_level
from shvatka.utils.exceptions import NotAuthorizedForEdit


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


async def get_all_my_free_levels(author: dto.Player, dao: MyLevelsGetter) -> list[dto.Level]:
    return list(filter(lambda l: l.game_id is None, await dao.get_all_my(author)))


async def get_by_id(id_: int, author: dto.Player, dao: LevelByIdGetter) -> dto.Level:
    level = await dao.get_by_id(id_)
    check_is_author(level, author)
    return level


def check_is_author(level: dto.Level, player: dto.Player):
    if level.author.id != player.id:
        raise NotAuthorizedForEdit(
            permission_name="game_edit", player=player, level=level,
        )
