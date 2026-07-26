from dataclasses import dataclass
from datetime import datetime

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
