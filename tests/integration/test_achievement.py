import pytest

from src.infrastructure.db.dao.holder import HolderDao
from src.core.models import dto
from src.core.models import enums
from src.core.services.achievement import add_achievement


@pytest.mark.asyncio
async def test_create_achievement(
    hermione: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    assert 0 == await check_dao.achievement.count()
    await add_achievement(hermione, enums.Achievement.game_name_joke, dao.achievement)
    assert 1 == await check_dao.achievement.count()
    (actual,) = await check_dao.achievement.get_by_player(hermione)  # type: dto.Achievement
    assert actual.player.id == hermione.id
    assert actual.name == enums.Achievement.game_name_joke
    assert actual.first


@pytest.mark.asyncio
async def test_create_second_achievement(
    hermione: dto.Player,
    ron: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    assert 0 == await check_dao.achievement.count()
    await add_achievement(hermione, enums.Achievement.game_name_joke, dao.achievement)
    await add_achievement(ron, enums.Achievement.game_name_joke, dao.achievement)
    assert 2 == await check_dao.achievement.count()
    (hermi_achievement,) = await check_dao.achievement.get_by_player(
        hermione
    )  # type: dto.Achievement
    assert hermi_achievement.player.id == hermione.id
    assert hermi_achievement.first
    (ron_achievement,) = await check_dao.achievement.get_by_player(ron)  # type: dto.Achievement
    assert ron_achievement.player.id == ron.id
    assert not ron_achievement.first
