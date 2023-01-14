from datetime import datetime, timedelta
from typing import Protocol

from shvatka.interfaces.dal.base import Committer
from shvatka.interfaces.dal.game import GameByIdGetter
from shvatka.models import dto


class LevelTestProtocolDao(Protocol, Committer):
    async def save_started_level_test(self, suite: dto.LevelTestSuite, now: datetime):
        raise NotImplementedError

    async def is_still_testing(self, suite: dto.LevelTestSuite) -> bool:
        raise NotImplementedError

    async def save_key(self, key: str, suite: dto.LevelTestSuite, is_correct: bool):
        raise NotImplementedError

    async def get_correct_tested_keys(self, suite: dto.LevelTestSuite) -> set[str]:
        raise NotImplementedError

    async def complete_test(self, suite: dto.LevelTestSuite):
        raise NotImplementedError

    async def get_testing_result(self, suite: dto.LevelTestSuite) -> timedelta:
        raise NotImplementedError


class LevelTestingDao(Protocol, LevelTestProtocolDao, GameByIdGetter):
    pass
