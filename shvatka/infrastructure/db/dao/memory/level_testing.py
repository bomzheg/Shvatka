from datetime import datetime

from shvatka.core.interfaces.dal.level_testing import LevelTestProtocolDao
from shvatka.core.models import dto
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc


class LevelTestingData(LevelTestProtocolDao):
    def __init__(self) -> None:
        self._buckets: dict[int, dict[int, dto.LevelTestBucket]] = {}

    async def save_started_level_test(self, suite: dto.LevelTestSuite, now: datetime):
        bucket = self._get_bucket(suite)
        if bucket.protocol.start is not None:
            raise exceptions.ActionCantBeNow(
                text="тестирование другого уровня уже начато",
                player=suite.tester.player,
                game=suite.tester.game,
            )
        bucket.protocol.start = now

    async def is_still_testing(self, suite: dto.LevelTestSuite) -> bool:
        bucket = self._get_bucket(suite)
        if bucket.protocol.start is None:
            return False
        return bucket.protocol.stop is None

    async def save_key(self, key: str, suite: dto.LevelTestSuite, is_correct: bool):
        bucket = self._get_bucket(suite)
        bucket.all_typed.append(
            dto.SimpleKey(text=key, is_correct=is_correct, at=datetime.now(tz=tz_utc))
        )
        if is_correct:
            bucket.correct_typed.add(key)

    async def get_correct_tested_keys(self, suite: dto.LevelTestSuite) -> set[str]:
        bucket = self._get_bucket(suite)
        return bucket.correct_typed

    async def complete_test(self, suite: dto.LevelTestSuite):
        bucket = self._get_bucket(suite)
        bucket.protocol.stop = datetime.now(tz=tz_utc)

    async def get_testing_result(self, suite: dto.LevelTestSuite) -> dto.LevelTestingResult:
        bucket = self._get_bucket(suite)
        assert bucket.protocol.start
        assert bucket.protocol.stop
        return dto.LevelTestingResult(bucket, bucket.protocol.stop - bucket.protocol.start)

    async def get_all_typed(self, suite: dto.LevelTestSuite) -> list[dto.SimpleKey]:
        bucket = self._get_bucket(suite)
        return bucket.all_typed

    async def cancel_test(self, suite: dto.LevelTestSuite):
        self._del_bucket(suite)

    def _get_bucket(self, suite: dto.LevelTestSuite) -> dto.LevelTestBucket:
        return self._buckets.setdefault(suite.level.db_id, {}).setdefault(
            suite.tester.player.id, dto.LevelTestBucket()
        )

    def _del_bucket(self, suite: dto.LevelTestSuite):
        self._buckets.setdefault(suite.level.db_id, {}).pop(suite.tester.player.id, None)

    async def delete_all(self):
        self._buckets.clear()

    async def commit(self) -> None:
        pass
