from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.played import Played
from shvatka.core.players.dto import TimelineItem as CoreTimelineItem


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
class RenameFile:
    filename: str


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
class NewTeam:
    name: str
    description: str | None = None


@dataclass
class WaiverVote:
    player_id: int
    played: Played = Played.yes


@dataclass
class ReplaceWaivers:
    waivers: list[WaiverVote] = field(default_factory=list)


@dataclass
class AdminGameScenarioEdit:
    scenario: dict[str, Any]
    author_id: int | None = None
    """when set, the game is reassigned to this player before the scenario is saved"""


@dataclass
class AdminChangeEmail:
    email: str
    verified: bool = False


@dataclass
class AdminChangeTg:
    tg_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


@dataclass
class MergeRequest:
    primary_id: int
    secondary_id: int
    """the record merged into primary and then deleted"""


@dataclass
class TimelineItem:
    team_id: int
    date_joined: datetime
    date_left: datetime | None = None
    role: str | None = None
    emoji: str | None = None
    permissions: dict[str, bool] | None = None

    def to_core(self) -> CoreTimelineItem:
        return CoreTimelineItem(
            team_id=self.team_id,
            date_joined=self.date_joined,
            date_left=self.date_left,
            role=self.role,
            emoji=self.emoji,
            permissions=self.permissions,
        )


@dataclass
class MergePlayersRequest(MergeRequest):
    timeline: list[TimelineItem] | None = None
    """manually built team history for the merged player; replaces both histories.
    Must not violate the waiver points of either player."""

    def core_timeline(self) -> list[CoreTimelineItem] | None:
        if self.timeline is None:
            return None
        return [item.to_core() for item in self.timeline]


@dataclass
class AcceptRequest:
    timeline: list[TimelineItem] | None = None
    """only for player merge requests: manually built team history replacing
    both players' histories when they are not compatible."""

    def core_timeline(self) -> list[CoreTimelineItem] | None:
        if self.timeline is None:
            return None
        return [item.to_core() for item in self.timeline]


@dataclass(frozen=True, slots=True)
class PushKeys:
    p256dh: str
    auth: str


@dataclass(frozen=True, slots=True)
class PushSubscription:
    endpoint: str
    keys: PushKeys


@dataclass
class MarkNotificationsRead:
    ids: list[int] = field(default_factory=list)


@dataclass
class TeamJoinInvite:
    team_id: int
    player_id: int
    role: str | None = None
    emoji: str | None = None


@dataclass
class TeamJoinRequest:
    team_id: int


@dataclass
class OrgInvite:
    game_id: int
    player_id: int
