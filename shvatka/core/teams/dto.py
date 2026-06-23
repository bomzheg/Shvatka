from dataclasses import dataclass

from shvatka.core.models import dto


@dataclass(frozen=True, slots=True)
class TeamWithStat:
    """A team together with aggregated statistics for list views."""

    team: dto.Team
    played_games_count: int


@dataclass(frozen=True, slots=True)
class TeamPlayerWithStat:
    """A team member together with aggregated statistics for list views."""

    team_player: dto.FullTeamPlayer
    played_games_count: int
