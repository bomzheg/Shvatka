import pytest

from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.services.achievement import add_achievement
from shvatka.infrastructure.db.dao.holder import HolderDao


@pytest.mark.asyncio
async def test_create_achievement(
    hermione: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    assert 0 == await check_dao.achievement.count()
    await add_achievement(hermione, enums.Achievement.game_name_joke, dao.achievement)
    assert 1 == await check_dao.achievement.count()
    actual, *_ = await check_dao.achievement.get_by_player(hermione)
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
    hermi_achievement, *_ = await check_dao.achievement.get_by_player(hermione)
    assert hermi_achievement.player.id == hermione.id
    assert hermi_achievement.first
    ron_achievement, *_ = await check_dao.achievement.get_by_player(ron)
    assert ron_achievement.player.id == ron.id
    assert not ron_achievement.first
