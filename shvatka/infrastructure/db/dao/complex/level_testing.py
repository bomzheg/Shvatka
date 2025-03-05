import typing
from dataclasses import dataclass
from datetime import datetime

from shvatka.core.interfaces.dal.level_testing import LevelTestingDao
from shvatka.core.models import dto

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class LevelTestComplex(LevelTestingDao):
    dao: "HolderDao"

    async def save_started_level_test(self, suite: dto.LevelTestSuite, now: datetime):
        return await self.dao.level_test.save_started_level_test(suite, now)

    async def is_still_testing(self, suite: dto.LevelTestSuite) -> bool:
        return await self.dao.level_test.is_still_testing(suite)

    async def save_key(self, key: str, suite: dto.LevelTestSuite, is_correct: bool):
        return await self.dao.level_test.save_key(key, suite, is_correct)

    async def get_correct_tested_keys(self, suite: dto.LevelTestSuite) -> set[str]:
        return await self.dao.level_test.get_correct_tested_keys(suite)

    async def complete_test(self, suite: dto.LevelTestSuite):
        return await self.dao.level_test.complete_test(suite)

    async def get_testing_result(self, suite: dto.LevelTestSuite) -> dto.LevelTestingResult:
        return await self.dao.level_test.get_testing_result(suite)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_=id_, author=author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_=id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)

    async def commit(self) -> None:
        return await self.dao.level_test.commit()
