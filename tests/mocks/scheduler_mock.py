from datetime import datetime

from shvatka.models import dto
from shvatka.scheduler import LevelTestScheduler


class LevelSchedulerMock(LevelTestScheduler):
    def __init__(self):
        self.calls = []

    async def plain_test_hint(self, suite: dto.LevelTestSuite, hint_number: int, run_at: datetime):
        self.calls.append((suite, hint_number, run_at))
