from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models.enums import GameStatus


@dataclass
class Key:
    text: str


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
class JoinTeam:
    player_id: int
    role: str | None = None
    emoji: str | None = None


@dataclass
class TeamPlayerSettings:
    role: str | None = None
    emoji: str | None = None
    permissions: dict[str, bool] | None = None


@dataclass
class TeamSettings:
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class PushKeys:
    p256dh: str
    auth: str


@dataclass(frozen=True, slots=True)
class PushSubscription:
    endpoint: str
    keys: PushKeys
