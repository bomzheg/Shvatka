from dataclasses import dataclass
from datetime import datetime

from shvatka.core.interfaces.dal.level_testing import LevelTestingDao
from shvatka.core.models import dto
from shvatka.infrastructure.db.dao import GameDao
from shvatka.infrastructure.db.dao.memory.level_testing import LevelTestingData


@dataclass
class LevelTestComplex(LevelTestingDao):
    game: GameDao
    level_testing: LevelTestingData

    async def save_started_level_test(self, suite: dto.LevelTestSuite, now: datetime):
        return await self.level_testing.save_started_level_test(suite, now)

    async def is_still_testing(self, suite: dto.LevelTestSuite) -> bool:
        return await self.level_testing.is_still_testing(suite)

    async def save_key(self, key: str, suite: dto.LevelTestSuite, is_correct: bool):
        return await self.level_testing.save_key(key, suite, is_correct)

    async def get_correct_tested_keys(self, suite: dto.LevelTestSuite) -> set[str]:
        return await self.level_testing.get_correct_tested_keys(suite)

    async def complete_test(self, suite: dto.LevelTestSuite):
        return await self.level_testing.complete_test(suite)

    async def get_testing_result(self, suite: dto.LevelTestSuite) -> dto.LevelTestingResult:
        return await self.level_testing.get_testing_result(suite)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.game.get_by_id(id_=id_, author=author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.game.get_full(id_=id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.game.add_levels(game)

    async def commit(self) -> None:
        return await self.level_testing.commit()
