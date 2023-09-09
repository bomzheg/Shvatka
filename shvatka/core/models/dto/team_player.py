from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .common import DateRange
from .player import Player
from .team import Team
from shvatka.core.models import enums


@dataclass
class TeamPlayer:
    id: int
    player_id: int
    team_id: int
    date_joined: datetime
    date_left: datetime | None
    role: str
    emoji: str

    _can_manage_waivers: bool
    _can_manage_players: bool
    _can_change_team_name: bool
    _can_add_players: bool
    _can_remove_players: bool

    def __eq__(self, other) -> bool:
        if not isinstance(other, TeamPlayer | FullTeamPlayer):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def get_permissions(self) -> dict[str, bool]:
        return {
            "can_manage_waivers": self._can_manage_waivers,
            "can_manage_players": self._can_remove_players,
            "can_change_team_name": self._can_change_team_name,
            "can_add_players": self._can_add_players,
            "can_remove_players": self._can_remove_players,
        }


@dataclass
class FullTeamPlayer(TeamPlayer):
    player: Player
    team: Team

    @property
    def is_captain(self):
        return self.team.captain.id == self.player_id

    @property
    def can_manage_waivers(self) -> bool:
        return self.is_captain or self._can_manage_waivers

    @property
    def can_manage_players(self) -> bool:
        return self.is_captain or self._can_manage_players

    @property
    def can_change_team_name(self) -> bool:
        return self.is_captain or self._can_change_team_name

    @property
    def can_add_players(self) -> bool:
        return self.is_captain or self._can_add_players

    @property
    def can_remove_players(self) -> bool:
        return self.is_captain or self._can_remove_players

    @property
    def permissions(self) -> dict[enums.TeamPlayerPermission, bool]:
        return {
            enums.TeamPlayerPermission.can_manage_waivers: self.can_manage_waivers,
            enums.TeamPlayerPermission.can_manage_players: self.can_manage_players,
            enums.TeamPlayerPermission.can_change_team_name: self.can_change_team_name,
            enums.TeamPlayerPermission.can_add_players: self.can_add_players,
            enums.TeamPlayerPermission.can_remove_players: self.can_remove_players,
        }

    @classmethod
    def from_simple(cls, team_player: TeamPlayer, player: Player, team: Team):
        assert team_player.team_id == team.id
        assert team_player.player_id == player.id
        return cls(
            id=team_player.id,
            player_id=team_player.player_id,
            team_id=team_player.team_id,
            date_joined=team_player.date_joined,
            date_left=team_player.date_left,
            role=team_player.role,
            emoji=team_player.emoji,
            _can_manage_waivers=team_player._can_manage_waivers,  # noqa: SLF001
            _can_manage_players=team_player._can_manage_players,  # noqa: SLF001
            _can_change_team_name=team_player._can_change_team_name,  # noqa: SLF001
            _can_add_players=team_player._can_add_players,  # noqa: SLF001
            _can_remove_players=team_player._can_remove_players,  # noqa: SLF001
            team=team,
            player=player,
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, TeamPlayer | FullTeamPlayer):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


@dataclass
class TeamDataRange:
    range: DateRange
    team_id: int

    @classmethod
    def from_team_player(cls, tp: TeamPlayer):
        return cls(range=DateRange(tp.date_joined, tp.date_left), team_id=tp.team_id)
