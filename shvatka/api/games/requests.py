from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from adaptix import Retort

from shvatka.core.models.dto.hints import AnyHint
from shvatka.core.models.enums import GameStatus


@dataclass
class NewGame:
    name: str


@dataclass
class GameStartAt:
    start_at: datetime | None = None


@dataclass
class GameStatusChange:
    status: GameStatus


@dataclass
class GameRelease:
    """The whole release of a game — replaces the published one."""

    hints: list[dict[str, Any]] = field(default_factory=list)

    def to_core(self, retort: Retort) -> list[AnyHint]:
        return retort.load(self.hints, list[AnyHint])


@dataclass
class Key:
    text: str


@dataclass
class NewOrg:
    player_id: int


@dataclass
class DeleteOrg:
    org_id: int


@dataclass
class OrgPermissionUpdate:
    permission: str
    value: bool
