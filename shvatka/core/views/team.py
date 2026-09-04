from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from shvatka.core.models import dto


class TeamNotifier(Protocol):
    async def notify(self, event: TeamEvent) -> None:
        raise NotImplementedError


@dataclass
class TeamEvent:
    team: dto.Team
    actor: dto.Player
    """The player who performed the action (inviter / remover / the player themselves)."""


@dataclass
class PlayerJoinedTeam(TeamEvent):
    invited: dto.Player

    @property
    def by_self(self) -> bool:
        return self.actor.id == self.invited.id


@dataclass
class PlayerLeftTeam(TeamEvent):
    removed: dto.Player

    @property
    def by_self(self) -> bool:
        return self.actor.id == self.removed.id


@dataclass
class CaptainChanged(TeamEvent):
    new_captain: dto.Player
    old_captain: dto.Player | None

    @property
    def by_old_captain(self) -> bool:
        return self.old_captain is not None and self.actor.id == self.old_captain.id


@dataclass
class TeamRenamed(TeamEvent):
    old_name: str

    @property
    def new_name(self) -> str:
        return self.team.name
