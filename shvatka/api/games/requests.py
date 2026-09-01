from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from adaptix import Retort

from shvatka.core.models.dto.hints import AnyHint, PhotoHint
from shvatka.core.models.enums import GameStatus


@dataclass
class NewGame:
    name: str


@dataclass
class GameName:
    """A new name for an existing game."""

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

    banner: dict[str, Any] | None = None
    """The wide title picture leading the release, with its caption."""
    hints: list[dict[str, Any]] = field(default_factory=list)

    def banner_to_core(self, retort: Retort) -> PhotoHint | None:
        return None if self.banner is None else retort.load(self.banner, PhotoHint)

    def hints_to_core(self, retort: Retort) -> list[AnyHint]:
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
