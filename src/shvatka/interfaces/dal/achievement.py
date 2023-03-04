from typing import Protocol

from src.shvatka.interfaces.dal.base import Committer
from src.shvatka.models import dto
from src.shvatka.models import enums


class AchievementAdder(Committer, Protocol):
    async def exist_type(self, achievement: enums.Achievement) -> bool:
        raise NotImplementedError

    async def add_achievement(self, achievement: dto.Achievement) -> None:
        raise NotImplementedError
