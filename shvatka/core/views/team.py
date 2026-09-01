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


@dataclass
class CaptainChanged(TeamEvent):
    """The team got a new captain.

    ``old_captain`` is ``None`` for a team that had none (an imported forum team,
    or one whose captain row was cleared).
    """

    new_captain: dto.Player
    old_captain: dto.Player | None

    @property
    def by_old_captain(self) -> bool:
        return self.old_captain is not None and self.actor.id == self.old_captain.id


@dataclass
class TeamRenamed(TeamEvent):
    """The team changed its name.

    ``team`` already carries the new name — ``old_name`` is the one it had
    before, so a notifier can tell what exactly changed.
    """

    old_name: str

    @property
    def new_name(self) -> str:
        return self.team.name
