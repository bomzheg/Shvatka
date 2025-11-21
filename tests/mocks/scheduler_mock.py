from datetime import datetime

from shvatka.core.interfaces.scheduler import LevelTestScheduler, Scheduler
from shvatka.core.models import dto
from shvatka.core.models.dto import action


class LevelSchedulerMock(LevelTestScheduler):
    def __init__(self) -> None:
        self.calls: list[tuple[dto.LevelTestSuite, int, datetime]] = []

    async def plain_test_hint(
        self, suite: dto.LevelTestSuite, hint_number: int, run_at: datetime
    ) -> None:
        self.calls.append((suite, hint_number, run_at))


class SchedulerMock(Scheduler):
    def __init__(self) -> None:
        self.plain_prepare_calls: list[dto.Game] = []
        self.plain_start_calls: list[dto.Game] = []
        self.plain_hint_calls: list[tuple[dto.Level, dto.Team, int, int, datetime]] = []
        self.cancel_scheduled_game_calls: list[dto.Game] = []

    def assert_one_planned_hint(self, level: dto.Level, team: dto.Team, hint_number: int) -> None:
        assert len(self.plain_hint_calls) == 1
        actual = self.plain_hint_calls.pop()
        assert (level, team, hint_number) == actual[:-2]
        assert isinstance(actual[-1], datetime)

    def assert_only_one_hint_for_team(
        self, level: dto.Level, team: dto.Team, hint_number: int
    ) -> None:
        assert len(self.plain_hint_calls) >= 1
        for i, (_, t, *_) in enumerate(self.plain_hint_calls):
            if t == team:
                actual = self.plain_hint_calls.pop(i)
                break
        else:
            raise AssertionError(f"No hint for team {team}")
        assert (level, team, hint_number) == actual[:-2]
        assert isinstance(actual[-1], datetime)

    def assert_no_unchecked(self):
        assert len(self.plain_hint_calls) == 0
        assert len(self.plain_start_calls) == 0
        assert len(self.plain_prepare_calls) == 0
        assert len(self.cancel_scheduled_game_calls) == 0

    async def plain_prepare(self, game: dto.Game) -> None:
        self.plain_prepare_calls.append(game)

    async def plain_start(self, game: dto.Game) -> None:
        self.plain_start_calls.append(game)

    async def plain_hint(
        self, level: dto.Level, team: dto.Team, hint_number: int, lt_id: int, run_at: datetime
    ) -> None:
        self.plain_hint_calls.append((level, team, hint_number, lt_id, run_at))

    async def cancel_scheduled_game(self, game: dto.Game) -> None:
        self.cancel_scheduled_game_calls.append(game)

    async def plain_level_event(self, team: dto.Team, lt_id: int, effects: action.Effects, run_at: datetime):
        pass
