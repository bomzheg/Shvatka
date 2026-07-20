from datetime import datetime, timedelta, timezone

import pytest

from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.played import Played
from shvatka.core.players.dto import (
    TimelineItem,
    WaiverPoint,
    WAIVER_POINT_BEFORE_GAME,
    WAIVER_POINT_AFTER_GAME,
    pending_game_interval,
)
from shvatka.core.players.player import (
    check_timeline_matches_points,
    get_waiver_points,
    normalize_timeline,
)
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_game

START_AT = datetime(2025, 4, 12, 16, 0, tzinfo=timezone.utc)  # Saturday
NOW = START_AT


def create_player(id_: int = 1) -> dto.Player:
    return dto.Player(id=id_, can_be_author=False, is_dummy=False, username=f"player{id_}")


def create_team(id_: int = 1) -> dto.Team:
    return dto.Team(id=id_, name=f"team {id_}", captain=None, is_dummy=False, description=None)


def create_game(
    id_: int = 1,
    start_at: datetime | None = START_AT,
    status: GameStatus = GameStatus.complete,
) -> dto.Game:
    return dto.Game(
        id=id_,
        author=create_player(100),
        name=f"game {id_}",
        status=status,
        manage_token="",
        start_at=start_at,
        number=id_,
        results=dto.GameResults(
            published_chanel_id=None, results_picture_file_id=None, keys_url=None
        ),
    )


def create_point(team: dto.Team, game: dto.Game) -> WaiverPoint:
    return WaiverPoint.from_waiver(
        dto.Waiver(player=create_player(), team=team, game=game, played=Played.yes),
        now=NOW,
    )


class FakeWaiversDao:
    def __init__(self, waivers: list[dto.Waiver]) -> None:
        self.waivers = waivers

    async def get_player_waivers(self, player: dto.Player) -> list[dto.Waiver]:
        return self.waivers


def test_waiver_point_interval():
    point = create_point(create_team(), create_game())
    assert point.at_since == START_AT - timedelta(hours=12)
    assert point.at_until == START_AT + timedelta(hours=48)
    assert point.at_since == START_AT - WAIVER_POINT_BEFORE_GAME
    assert point.at_until == START_AT + WAIVER_POINT_AFTER_GAME


def test_pending_game_interval_regular_day():
    # Saturday 19:00 MSK -> the point is the current week (Mon 07.04 .. Mon 14.04)
    since, until = pending_game_interval(NOW)
    assert since == datetime(2025, 4, 7, tzinfo=tz_game)
    assert until == datetime(2025, 4, 14, tzinfo=tz_game)


def test_pending_game_interval_sunday():
    # Sunday -> the game is likely next week: today .. end of the next week
    sunday = datetime(2025, 4, 13, 12, 0, tzinfo=tz_game)
    since, until = pending_game_interval(sunday)
    assert since == datetime(2025, 4, 13, tzinfo=tz_game)
    assert until == datetime(2025, 4, 21, tzinfo=tz_game)


def test_waiver_point_for_pending_game():
    game = create_game(start_at=None, status=GameStatus.getting_waivers)
    point = create_point(create_team(), game)
    assert point.at_since == datetime(2025, 4, 7, tzinfo=tz_game)
    assert point.at_until == datetime(2025, 4, 14, tzinfo=tz_game)


@pytest.mark.asyncio
async def test_get_waiver_points_skips_unplayed_and_undated():
    team = create_team()
    player = create_player()
    dao = FakeWaiversDao(
        [
            dto.Waiver(player=player, team=team, game=create_game(1), played=Played.yes),
            dto.Waiver(player=player, team=team, game=create_game(2), played=Played.no),
            dto.Waiver(player=player, team=team, game=create_game(3), played=Played.revoked),
            dto.Waiver(
                player=player, team=team, game=create_game(4, start_at=None), played=Played.yes
            ),
        ]
    )
    points = await get_waiver_points(player, dao, now=NOW)
    assert len(points) == 1
    assert points[0].game.id == 1


@pytest.mark.asyncio
async def test_get_waiver_points_includes_pending_game():
    team = create_team()
    player = create_player()
    game = create_game(start_at=None, status=GameStatus.getting_waivers)
    dao = FakeWaiversDao([dto.Waiver(player=player, team=team, game=game, played=Played.yes)])
    points = await get_waiver_points(player, dao, now=NOW)
    assert len(points) == 1
    assert points[0].at_since == datetime(2025, 4, 7, tzinfo=tz_game)


def test_normalize_timeline_sorts():
    timeline = normalize_timeline(
        [
            TimelineItem(team_id=2, date_joined=START_AT + timedelta(days=10)),
            TimelineItem(
                team_id=1,
                date_joined=START_AT - timedelta(days=10),
                date_left=START_AT + timedelta(days=5),
            ),
        ]
    )
    assert [item.team_id for item in timeline] == [1, 2]


def test_normalize_timeline_rejects_empty():
    with pytest.raises(exceptions.MergeError):
        normalize_timeline([])


def test_normalize_timeline_rejects_naive_datetime():
    naive = START_AT.replace(tzinfo=None)
    with pytest.raises(exceptions.MergeError):
        normalize_timeline([TimelineItem(team_id=1, date_joined=naive)])


def test_normalize_timeline_rejects_unknown_permission():
    with pytest.raises(exceptions.MergeError):
        normalize_timeline(
            [
                TimelineItem(
                    team_id=1, date_joined=START_AT, permissions={"can_fly_broomstick": True}
                ),
            ]
        )


def test_normalize_timeline_rejects_left_before_joined():
    with pytest.raises(exceptions.MergeError):
        normalize_timeline(
            [
                TimelineItem(
                    team_id=1, date_joined=START_AT, date_left=START_AT - timedelta(days=1)
                ),
            ]
        )


def test_normalize_timeline_rejects_overlap():
    with pytest.raises(exceptions.MergeError):
        normalize_timeline(
            [
                TimelineItem(
                    team_id=1, date_joined=START_AT, date_left=START_AT + timedelta(days=2)
                ),
                TimelineItem(team_id=2, date_joined=START_AT + timedelta(days=1)),
            ]
        )


def test_normalize_timeline_rejects_open_interval_before_next():
    with pytest.raises(exceptions.MergeError):
        normalize_timeline(
            [
                TimelineItem(team_id=1, date_joined=START_AT),
                TimelineItem(team_id=2, date_joined=START_AT + timedelta(days=1)),
            ]
        )


def test_timeline_covering_point_passes():
    team = create_team(1)
    point = create_point(team, create_game())
    timeline = [
        TimelineItem(
            team_id=1,
            date_joined=START_AT - timedelta(days=1),
            date_left=START_AT + timedelta(days=3),
        ),
        TimelineItem(team_id=2, date_joined=START_AT + timedelta(days=3)),
    ]
    check_timeline_matches_points(timeline, [point])


def test_timeline_with_wrong_team_fails():
    point = create_point(create_team(1), create_game())
    timeline = [TimelineItem(team_id=2, date_joined=START_AT - timedelta(days=1))]
    with pytest.raises(exceptions.MergeError):
        check_timeline_matches_points(timeline, [point])


def test_timeline_partially_covering_point_fails():
    point = create_point(create_team(1), create_game())
    # joined after the protected interval started
    timeline = [TimelineItem(team_id=1, date_joined=START_AT - timedelta(hours=1))]
    with pytest.raises(exceptions.MergeError):
        check_timeline_matches_points(timeline, [point])


def test_timeline_leaving_too_early_fails():
    point = create_point(create_team(1), create_game())
    timeline = [
        TimelineItem(
            team_id=1,
            date_joined=START_AT - timedelta(days=1),
            date_left=START_AT + timedelta(hours=1),
        ),
    ]
    with pytest.raises(exceptions.MergeError):
        check_timeline_matches_points(timeline, [point])
