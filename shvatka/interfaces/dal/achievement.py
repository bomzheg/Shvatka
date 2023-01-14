from typing import Protocol

from shvatka.interfaces.dal.base import Committer
from shvatka.models import enums, dto


class AchievementAdder(Protocol, Committer):
    async def exist_type(self, achievement: enums.Achievement) -> bool:
        raise NotImplementedError

    async def add_achievement(self, achievement: dto.Achievement) -> None:
        raise NotImplementedError
