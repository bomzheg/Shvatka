from dataclasses import dataclass
from datetime import datetime

from shvatka.api.shared.responses import Player
from shvatka.core.models import dto
from shvatka.core.teams.dto import CaptainedTeam as CaptainedTeamDto
from shvatka.core.teams.dto import TeamPlayerWithStat as TeamPlayerWithStatDto
from shvatka.core.teams.dto import TeamWithStat as TeamWithStatDto


@dataclass
class TeamWithStat:
    id: int
    name: str
    captain_id: int | None
    captain: Player | None
    description: str | None
    played_games_count: int

    @classmethod
    def from_core(cls, core: TeamWithStatDto) -> "TeamWithStat":
        return cls(
            id=core.team.id,
            name=core.team.name,
            captain_id=core.team.captain_id,
            captain=Player.from_core(core.team.captain) if core.team.captain else None,
            description=core.team.description,
            played_games_count=core.played_games_count,
        )


@dataclass
class CaptainedTeam:
    id: int
    name: str
    captain_id: int | None
    captain: Player | None
    description: str | None
    played_games_count: int
    is_current: bool
    """Whether the captain plays in this team right now, or only leads it."""

    @classmethod
    def from_core(cls, core: CaptainedTeamDto) -> "CaptainedTeam":
        return cls(
            id=core.team.id,
            name=core.team.name,
            captain_id=core.team.captain_id,
            captain=Player.from_core(core.team.captain) if core.team.captain else None,
            description=core.team.description,
            played_games_count=core.played_games_count,
            is_current=core.is_current,
        )


@dataclass
class TeamMember:
    team_player_id: int
    id: int
    username: str | None
    can_be_author: bool
    emoji: str | None
    role: str
    permissions: dict[str, bool]
    date_joined: datetime

    @classmethod
    def from_core(cls, core: dto.FullTeamPlayer) -> "TeamMember":
        return cls(
            team_player_id=core.id,
            id=core.player.id,
            username=core.player.username,
            can_be_author=core.player.can_be_author,
            emoji=core.emoji,
            role=core.role,
            permissions={permission.name: value for permission, value in core.permissions.items()},
            date_joined=core.date_joined,
        )


@dataclass
class TeamMemberWithStat:
    team_player_id: int
    id: int
    username: str | None
    can_be_author: bool
    emoji: str | None
    role: str
    permissions: dict[str, bool]
    date_joined: datetime
    played_games_count: int

    @classmethod
    def from_core(cls, core: TeamPlayerWithStatDto) -> "TeamMemberWithStat":
        tp = core.team_player
        return cls(
            team_player_id=tp.id,
            id=tp.player.id,
            username=tp.player.username,
            can_be_author=tp.player.can_be_author,
            emoji=tp.emoji,
            role=tp.role,
            permissions={permission.name: value for permission, value in tp.permissions.items()},
            date_joined=tp.date_joined,
            played_games_count=core.played_games_count,
        )
