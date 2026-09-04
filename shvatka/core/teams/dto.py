from dataclasses import dataclass

from shvatka.core.models import dto


@dataclass(frozen=True, slots=True)
class TeamWithStat:
    team: dto.Team
    played_games_count: int


@dataclass(frozen=True, slots=True)
class CaptainedTeam:
    team: dto.Team
    played_games_count: int
    is_current: bool


@dataclass(frozen=True, slots=True)
class TeamPlayerWithStat:
    team_player: dto.FullTeamPlayer
    played_games_count: int
