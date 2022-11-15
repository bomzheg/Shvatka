from dataclasses import dataclass, field
from datetime import timedelta, datetime

from shvatka.dal.level_testing import LevelTestProtocolDao
from shvatka.models import dto


@dataclass
class SimpleKey:
    text: str
    at: datetime
    is_correct: bool


@dataclass
class LevelTestProtocol:
    start: datetime | None = None
    stop: datetime | None = None


@dataclass
class LevelTestBucket:
    protocol: LevelTestProtocol = field(default_factory=LevelTestProtocol)
    correct_typed: set[str] = field(default_factory=set)
    all_typed: list[SimpleKey] = field(default_factory=list)


class LevelTestingData(LevelTestProtocolDao):
    def __init__(self):
        self._buckets: dict[int, dict[int, LevelTestBucket]] = {}

    async def save_started_level_test(self, suite: dto.LevelTestSuite, now: datetime):
        bucket = self._get_bucket(suite)
        assert bucket.protocol.start is None
        bucket.protocol.start = now

    async def is_still_testing(self, suite: dto.LevelTestSuite) -> bool:
        bucket = self._get_bucket(suite)
        if bucket.protocol.start is None:
            return False
        return bucket.protocol.stop is None

    async def save_key(self, key: str, suite: dto.LevelTestSuite, is_correct: bool):
        bucket = self._get_bucket(suite)
        bucket.all_typed.append(SimpleKey(text=key, is_correct=is_correct, at=datetime.utcnow()))
        if is_correct:
            bucket.correct_typed.add(key)

    async def get_correct_tested_keys(self, suite: dto.LevelTestSuite) -> set[str]:
        bucket = self._get_bucket(suite)
        return bucket.correct_typed

    async def complete_test(self, suite: dto.LevelTestSuite):
        bucket = self._get_bucket(suite)
        bucket.protocol.stop = datetime.utcnow()

    async def get_testing_result(self, suite: dto.LevelTestSuite) -> timedelta:
        bucket = self._get_bucket(suite)
        return bucket.protocol.stop - bucket.protocol.start

    async def get_all_typed(self, suite: dto.LevelTestSuite) -> list[SimpleKey]:
        bucket = self._get_bucket(suite)
        return bucket.all_typed

    def _get_bucket(self, suite: dto.LevelTestSuite) -> LevelTestBucket:
        return self._buckets\
            .setdefault(suite.level.db_id, {})\
            .setdefault(suite.tester.player.id, LevelTestBucket())

    async def delete_all(self):
        self._buckets.clear()

    async def commit(self) -> None:
        pass


