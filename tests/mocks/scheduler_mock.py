from datetime import datetime

from shvatka.core.interfaces.scheduler import LevelTestScheduler, Scheduler
from shvatka.core.models import dto


class LevelSchedulerMock(LevelTestScheduler):
    def __init__(self):
        self.calls = []

    async def plain_test_hint(self, suite: dto.LevelTestSuite, hint_number: int, run_at: datetime):
        self.calls.append((suite, hint_number, run_at))


class SchedulerMock(Scheduler):
    def __init__(self):
        self.calls = {}
        self.plain_prepare_calls: list[dto.Game] = []
        self.plain_start_calls: list[dto.Game] = []
        self.plain_hint_calls: list[tuple[dto.Level, dto.Team, int, datetime]] = []
        self.cancel_scheduled_game_calls: list[dto.Game] = []

    def assert_one_planned_hint(self, level: dto.Level, team: dto.Team, hint_number: int):
        assert len(self.plain_hint_calls) == 1
        actual = self.plain_hint_calls.pop()
        assert (level, team, hint_number) == actual[:-1]
        assert isinstance(actual[-1], datetime)

    async def plain_prepare(self, game: dto.Game):
        self.plain_prepare_calls.append(game)

    async def plain_start(self, game: dto.Game):
        self.plain_start_calls.append(game)

    async def plain_hint(
        self, level: dto.Level, team: dto.Team, hint_number: int, run_at: datetime
    ):
        self.plain_hint_calls.append((level, team, hint_number, run_at))

    async def cancel_scheduled_game(self, game: dto.Game):
        self.cancel_scheduled_game_calls.append(game)
