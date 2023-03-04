from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.models import dto
from shvatka.core.models import enums


class AchievementAdder(Committer, Protocol):
    async def exist_type(self, achievement: enums.Achievement) -> bool:
        raise NotImplementedError

    async def add_achievement(self, achievement: dto.Achievement) -> None:
        raise NotImplementedError
