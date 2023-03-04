from typing import Protocol

from src.core.interfaces.dal.base import Committer
from src.core.models import dto
from src.core.models import enums


class AchievementAdder(Committer, Protocol):
    async def exist_type(self, achievement: enums.Achievement) -> bool:
        raise NotImplementedError

    async def add_achievement(self, achievement: dto.Achievement) -> None:
        raise NotImplementedError
