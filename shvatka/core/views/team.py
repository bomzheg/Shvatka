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
    """A player joined (or was added to) a team."""

    invited: dto.Player

    @property
    def by_self(self) -> bool:
        return self.actor.id == self.invited.id


@dataclass
class PlayerLeftTeam(TeamEvent):
    """A player left a team (by themselves or was removed by a manager)."""

    removed: dto.Player

    @property
    def by_self(self) -> bool:
        return self.actor.id == self.removed.id
