from dataclasses import dataclass

from shvatka.core.models import dto


@dataclass(frozen=True, slots=True)
class TeamWithStat:
    """A team together with aggregated statistics for list views."""

    team: dto.Team
    played_games_count: int


@dataclass(frozen=True, slots=True)
class CaptainedTeam:
    """A team the player is the captain of, and whether they play in it right now.

    A captain keeps the captaincy of a team they left, so the two can differ: the
    web ui uses ``is_current`` to decide between "вы здесь" and a join button.
    """

    team: dto.Team
    played_games_count: int
    is_current: bool


@dataclass(frozen=True, slots=True)
class TeamPlayerWithStat:
    """A team member together with aggregated statistics for list views."""

    team_player: dto.FullTeamPlayer
    played_games_count: int
