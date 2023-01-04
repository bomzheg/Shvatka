from datetime import datetime

from shvatka.interfaces.scheduler import LevelTestScheduler, Scheduler
from shvatka.models import dto


class LevelSchedulerMock(LevelTestScheduler):
    def __init__(self):
        self.calls = []

    async def plain_test_hint(self, suite: dto.LevelTestSuite, hint_number: int, run_at: datetime):
        self.calls.append((suite, hint_number, run_at))


class SchedulerMock(Scheduler):
    def __init__(self):
        self.calls = {}

    async def plain_prepare(self, game: dto.Game):
        self.calls.setdefault("plain_prepare", []).append(game)

    async def plain_start(self, game: dto.Game):
        self.calls.setdefault("plain_game", []).append(game)

    async def plain_hint(
        self, level: dto.Level, team: dto.Team, hint_number: int, run_at: datetime
    ):
        self.calls.setdefault("plain_hint", []).append((level, team, hint_number, run_at))

    async def cancel_scheduled_game(self, game: dto.Game):
        self.calls.setdefault("cancel_scheduled_game", []).append(game)
