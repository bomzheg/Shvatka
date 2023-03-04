from shvatka.core.interfaces.dal.achievement import AchievementAdder
from shvatka.core.models import dto
from shvatka.core.models import enums


async def add_achievement(player: dto.Player, name: enums.Achievement, dao: AchievementAdder):
    first = not await dao.exist_type(name)
    achievement_result = dto.Achievement(player=player, name=name, first=first)
    await dao.add_achievement(achievement_result)
    await dao.commit()
