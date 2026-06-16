from dataclasses import dataclass, field
from datetime import datetime

from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.played import Played


@dataclass
class Key:
    text: str


@dataclass
class NewGame:
    name: str


@dataclass
class ChangeUsername:
    username: str


@dataclass
class GameStartAt:
    start_at: datetime | None = None


@dataclass
class GameStatusChange:
    status: GameStatus


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


@dataclass
class WaiverVote:
    player_id: int
    played: Played = Played.yes


@dataclass
class ReplaceWaivers:
    waivers: list[WaiverVote] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PushKeys:
    p256dh: str
    auth: str


@dataclass(frozen=True, slots=True)
class PushSubscription:
    endpoint: str
    keys: PushKeys
