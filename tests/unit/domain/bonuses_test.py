from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from shvatka.core.games.dto import BonusEvent, BonusSource
from shvatka.core.games.results import (
    TeamLevels,
    resolve_bonus_levels,
    route_bonuses,
    to_results,
)
from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.utils.datetime_utils import tz_utc

BASE_TIME = datetime(2026, 7, 26, 20, 0, tzinfo=tz_utc)


@pytest.fixture
def team() -> dto.Team:
    return dto.Team(id=1, name="Gryffindor", is_dummy=False, description=None)


@pytest.fixture
def level_times(team: dto.Team) -> list[dto.LevelTime]:
    """Level 0 took 20 minutes, level 1 took 10, then the finish."""
    return [
        _level_time(id_=10, team=team, level_number=0, offset=0),
        _level_time(id_=11, team=team, level_number=1, offset=20),
        _level_time(id_=12, team=team, level_number=2, offset=30),
    ]


def _level_time(id_: int, team: dto.Team, level_number: int, offset: int) -> dto.LevelTime:
    # computing bonuses never reads the game, so it is not needed here
    return dto.LevelTime(
        id=id_,
        game=None,
        team=team,
        level_number=level_number,
        start_at=BASE_TIME + timedelta(minutes=offset),
    )


def _bonus(
    minutes: float,
    level_time_id: int | None = 10,
    offset: int = 5,
    source: BonusSource = BonusSource.key,
    key: str | None = "SHБОНУС",
) -> BonusEvent:
    return BonusEvent(
        at=BASE_TIME + timedelta(minutes=offset),
        effects=action.Effects(id=uuid4(), bonus_minutes=minutes),
        source=source,
        key=key,
        level_time_id=level_time_id,
    )


def test_bonus_resolved_to_level_of_its_level_time(level_times: list[dto.LevelTime]):
    resolved = resolve_bonus_levels(level_times, [_bonus(5.0, level_time_id=11)])
    assert [b.level_number for b in resolved] == [1]


def test_bonus_without_level_time_resolved_by_time(level_times: list[dto.LevelTime]):
    """level_time_id is nullable in the DB — then the level comes from the event time."""
    resolved = resolve_bonus_levels(
        level_times,
        [
            _bonus(5.0, level_time_id=None, offset=5),
            _bonus(5.0, level_time_id=None, offset=25),
            _bonus(5.0, level_time_id=None, offset=35),
        ],
    )
    assert [b.level_number for b in resolved] == [0, 1, 2]


def test_bonus_of_unknown_level_time_falls_back_to_time(level_times: list[dto.LevelTime]):
    """A reference to someone else's level_time must not lose the bonus."""
    resolved = resolve_bonus_levels(level_times, [_bonus(5.0, level_time_id=999, offset=25)])
    assert [b.level_number for b in resolved] == [1]


def test_bonus_before_game_start_stays_without_level(level_times: list[dto.LevelTime]):
    resolved = resolve_bonus_levels(level_times, [_bonus(5.0, level_time_id=None, offset=-10)])
    assert [b.level_number for b in resolved] == [None]


def test_route_bonuses_groups_by_level(level_times: list[dto.LevelTime]):
    routed = route_bonuses(
        level_times,
        [
            _bonus(5.0, level_time_id=10),
            _bonus(-3.0, level_time_id=10),
            _bonus(2.0, level_time_id=11),
            _bonus(1.0, level_time_id=None, offset=-10),
        ],
    )
    assert sorted(routed, key=lambda k: (k is None, k)) == [0, 1, None]
    assert [b.minutes for b in routed[0]] == [5.0, -3.0]
    assert [b.minutes for b in routed[1]] == [2.0]
    assert [b.minutes for b in routed[None]] == [1.0]


def test_source_and_key_survive_routing(level_times: list[dto.LevelTime]):
    routed = route_bonuses(
        level_times,
        [
            _bonus(5.0, source=BonusSource.timer, key=None),
            _bonus(-3.0, source=BonusSource.key, key="SHШТРАФ"),
        ],
    )
    assert [(b.source, b.key) for b in routed[0]] == [
        (BonusSource.timer, None),
        (BonusSource.key, "SHШТРАФ"),
    ]


class TestTeamLevelsBonuses:
    def test_no_bonuses_at_all(self, team: dto.Team, level_times: list[dto.LevelTime]):
        team_levels = self._to_team_levels(team, level_times, None)
        assert team_levels.bonuses == {}
        assert team_levels.get_total_bonus() == timedelta()
        assert team_levels.get_level_bonus(0) == timedelta()

    def test_bonus_and_penalty_on_same_level_are_summed(
        self, team: dto.Team, level_times: list[dto.LevelTime]
    ):
        team_levels = self._to_team_levels(
            team, level_times, [_bonus(5.0, level_time_id=10), _bonus(-3.0, level_time_id=10)]
        )
        assert team_levels.get_level_bonus(0) == timedelta(minutes=2)

    def test_penalty_is_negative(self, team: dto.Team, level_times: list[dto.LevelTime]):
        team_levels = self._to_team_levels(team, level_times, [_bonus(-3.0, level_time_id=10)])
        assert team_levels.get_level_bonus(0) == timedelta(minutes=-3)

    def test_total_includes_bonuses_without_level(
        self, team: dto.Team, level_times: list[dto.LevelTime]
    ):
        """A bonus whose level is unresolved still lands in the total."""
        team_levels = self._to_team_levels(
            team,
            level_times,
            [_bonus(5.0, level_time_id=10), _bonus(7.0, level_time_id=None, offset=-10)],
        )
        assert team_levels.get_level_bonus(0) == timedelta(minutes=5)
        assert team_levels.get_total_bonus() == timedelta(minutes=12)

    def test_bonus_bigger_than_level_duration_goes_negative(
        self, team: dto.Team, level_times: list[dto.LevelTime]
    ):
        """Level 1 lasted 10 minutes, the bonus is 15 — not clamped, shown negative."""
        team_levels = self._to_team_levels(team, level_times, [_bonus(15.0, level_time_id=11)])
        raw = team_levels.get_level_timedelta(1)
        assert raw is not None
        assert raw.td - team_levels.get_level_bonus(1) == timedelta(minutes=-5)

    def test_sum_of_level_bonuses_equals_total(
        self, team: dto.Team, level_times: list[dto.LevelTime]
    ):
        """Additivity: the per-level sum must match the total."""
        team_levels = self._to_team_levels(
            team,
            level_times,
            [
                _bonus(5.0, level_time_id=10),
                _bonus(-3.0, level_time_id=11),
                _bonus(2.0, level_time_id=12),
            ],
        )
        by_levels = sum(
            (team_levels.get_level_bonus(level) for level in (0, 1, 2)),
            start=timedelta(),
        )
        assert by_levels == team_levels.get_total_bonus() == timedelta(minutes=4)

    @staticmethod
    def _to_team_levels(
        team: dto.Team,
        level_times: list[dto.LevelTime],
        bonuses: list[BonusEvent] | None,
    ) -> TeamLevels:
        results = to_results(
            dto.GameStat(level_times={team: level_times}),
            {team.id: bonuses} if bonuses else None,
        )
        return results.data[0]
