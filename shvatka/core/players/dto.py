from dataclasses import dataclass
from datetime import datetime, timedelta

from shvatka.core.models import dto

WAIVER_POINT_BEFORE_GAME = timedelta(hours=12)
WAIVER_POINT_AFTER_GAME = timedelta(hours=48)


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
    def from_waiver(cls, waiver: dto.Waiver) -> "WaiverPoint":
        if waiver.game.start_at is None:
            raise ValueError("can't build waiver point for game without start_at")
        return cls(
            game=waiver.game,
            team=waiver.team,
            at_since=waiver.game.start_at - WAIVER_POINT_BEFORE_GAME,
            at_until=waiver.game.start_at + WAIVER_POINT_AFTER_GAME,
        )


@dataclass(frozen=True, slots=True)
class TimelineItem:
    """One interval of a manually built team membership history."""

    team_id: int
    date_joined: datetime
    date_left: datetime | None = None


@dataclass(frozen=True, slots=True)
class PlayerStat:
    """Aggregated player statistics for the web UI.

    Includes the player together with key counters, the full history of team
    memberships and the list of games the player took part in.
    """

    player: dto.PlayerWithStat
    team_history: list[dto.FullTeamPlayer]
    played_games: list[dto.Game]
