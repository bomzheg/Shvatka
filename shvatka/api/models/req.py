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


@dataclass(frozen=True, slots=True)
class PushKeys:
    p256dh: str
    auth: str


@dataclass(frozen=True, slots=True)
class PushSubscription:
    endpoint: str
    keys: PushKeys
