from dataclass_factory import Factory

from shvatka.core.interfaces.dal.level import (
    LevelUpserter,
    MyLevelsGetter,
    LevelByIdGetter,
    LevelUnlinker,
)
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.services.player import check_allow_be_author
from shvatka.core.services.scenario.level_ops import load_level
from shvatka.core.utils.exceptions import NotAuthorizedForEdit, SHDataBreach


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


async def unlink_level(level: dto.Level, dao: LevelUnlinker):
    await dao.unlink(level)
    await dao.commit()


async def get_all_my_free_levels(author: dto.Player, dao: MyLevelsGetter) -> list[dto.Level]:
    return list(filter(lambda level: level.game_id is None, await dao.get_all_my(author)))


async def get_by_id(id_: int, author: dto.Player, dao: LevelByIdGetter) -> dto.Level:
    level = await dao.get_by_id(id_)
    check_is_author(level, author)
    return level


async def get_level_by_id_for_org(
    id_: int, org: dto.SecondaryOrganizer, dao: LevelByIdGetter
) -> dto.Level:
    level = await dao.get_by_id(id_=id_)
    check_is_org(level, org)
    return level


def check_is_author(level: dto.Level, player: dto.Player):
    if level.author.id != player.id:
        raise NotAuthorizedForEdit(
            permission_name="game_edit",
            player=player,
            level=level,
        )


def check_is_org(level: dto.Level, org: dto.SecondaryOrganizer):
    if level.game_id != org.game.id or org.deleted:
        raise NotAuthorizedForEdit(
            permission_name="game_edit",
            player=org.player,
            level=level,
        )


def check_can_link_to_game(game: dto.Game, level: dto.Level, author: dto.Player = None):
    if level.game_id is not None and level.game_id != game.id:
        raise SHDataBreach(
            player=author,
            notify_user=f"уровень {level.name_id} привязан к другой игре",
        )
