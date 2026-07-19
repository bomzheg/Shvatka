from dataclasses import dataclass
from datetime import datetime, time, timedelta

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_game

WAIVER_POINT_BEFORE_GAME = timedelta(hours=12)
WAIVER_POINT_AFTER_GAME = timedelta(hours=48)
SUNDAY = 6


@dataclass(frozen=True, slots=True)
class PlayerMainInfo:
    """Main info about a player together with their current team membership."""

    player: dto.Player
    team_player: dto.FullTeamPlayer | None


@dataclass(frozen=True, slots=True)
class PlayerIdentitiesInfo:
    """A player together with their email account (telegram/forum live on the player)."""

    player: dto.Player
    email: dto.EmailAccount | None


@dataclass(frozen=True, slots=True)
class WaiverPoint:
    """An interval during which a merged timeline must keep the player in the given team.

    Derived from a waiver: around the game start (``start_at - 12h`` .. ``start_at + 48h``)
    the player provably acted as a member of that team, so any manually built
    team history must cover the whole interval with that team.
    """

    game: dto.Game
    team: dto.Team
    at_since: datetime
    at_until: datetime

    @classmethod
    def from_waiver(cls, waiver: dto.Waiver, now: datetime) -> "WaiverPoint":
        if waiver.game.start_at is not None:
            at_since = waiver.game.start_at - WAIVER_POINT_BEFORE_GAME
            at_until = waiver.game.start_at + WAIVER_POINT_AFTER_GAME
        elif waiver.game.is_getting_waivers():
            at_since, at_until = pending_game_interval(now)
        else:
            raise ValueError("can't build waiver point for game without start_at")
        return cls(
            game=waiver.game,
            team=waiver.team,
            at_since=at_since,
            at_until=at_until,
        )


def pending_game_interval(now: datetime) -> tuple[datetime, datetime]:
    """The interval fixed by a waiver for a game that is still getting waivers.

    The game has no start date yet, so assume it happens this week: the point is
    the current week. On Sunday the game is likely next week, so the point spans
    from today until the end of the next week.
    """
    today = now.astimezone(tz_game).date()
    if today.weekday() == SUNDAY:
        since_day = today
        until_day = today + timedelta(days=8)
    else:
        since_day = today - timedelta(days=today.weekday())
        until_day = since_day + timedelta(days=7)
    return (
        datetime.combine(since_day, time.min, tzinfo=tz_game),
        datetime.combine(until_day, time.min, tzinfo=tz_game),
    )


@dataclass(frozen=True, slots=True)
class TimelineItem:
    """One interval of a manually built team membership history.

    Role, emoji and permissions are set explicitly by the admin; unset values
    fall back to the same defaults as a regular team join.
    """

    team_id: int
    date_joined: datetime
    date_left: datetime | None = None
    role: str | None = None
    emoji: str | None = None
    permissions: dict[str, bool] | None = None


@dataclass(frozen=True, slots=True)
class PlayerStat:
    """Aggregated player statistics for the web UI.

    Includes the player together with key counters, the full history of team
    memberships and the list of games the player took part in.
    """

    player: dto.PlayerWithStat
    team_history: list[dto.FullTeamPlayer]
    played_games: list[dto.Game]
