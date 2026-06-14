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
    player: dto.Player


@dataclass
class PlayerJoinedTeam(TeamEvent):
    """A player joined (or was added to) a team."""

    inviter: dto.Player

    @property
    def by_self(self) -> bool:
        return self.inviter.id == self.player.id


@dataclass
class PlayerLeftTeam(TeamEvent):
    """A player left a team (by themselves or was removed by a manager)."""

    remover: dto.Player

    @property
    def by_self(self) -> bool:
        return self.remover.id == self.player.id
