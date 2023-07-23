from dataclass_factory import Factory

from shvatka.core.interfaces.dal.level import (
    LevelUpserter,
    MyLevelsGetter,
    LevelByIdGetter,
    LevelCorrectUnlinker,
    LevelDeleter,
)
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.rules.level import check_is_author, check_is_org, check_can_edit
from shvatka.core.services.player import check_allow_be_author
from shvatka.core.services.scenario.level_ops import load_level


async def upsert_raw_level(
    level_data: dict, author: dto.Player, dcf: Factory, dao: LevelUpserter
) -> dto.Level:
    check_allow_be_author(author)
    scenario = load_level(level_data, dcf)
    return await upsert_level(author, scenario, dao)


async def upsert_level(author: dto.Player, scenario: scn.LevelScenario, dao: LevelUpserter):
    check_allow_be_author(author)
    result = await dao.upsert(author, scenario)
    await dao.commit()
    return result


async def unlink_level(level: dto.Level, author: dto.Player, dao: LevelCorrectUnlinker):
    check_can_edit(level, author)
    game_id = level.game_id
    await dao.unlink(level)
    if game_id:
        await dao.update_number_in_game(game_id)
    await dao.commit()


async def get_all_my_free_levels(author: dto.Player, dao: MyLevelsGetter) -> list[dto.Level]:
    return list(filter(lambda level: level.game_id is None, await dao.get_all_my(author)))


async def get_by_id(id_: int, author: dto.Player, dao: LevelByIdGetter) -> dto.Level:
    level = await dao.get_by_id(id_)
    check_is_author(level, author)
    return level


async def delete_level(level: dto.Level, author: dto.Player, dao: LevelDeleter) -> None:
    check_can_edit(level, author)
    await dao.delete(level.db_id)
    await dao.commit()


async def get_level_by_id_for_org(
    id_: int, org: dto.SecondaryOrganizer, dao: LevelByIdGetter
) -> dto.Level:
    level = await dao.get_by_id(id_=id_)
    check_is_org(level, org)
    return level
