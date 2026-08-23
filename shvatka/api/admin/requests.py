from dataclasses import dataclass
from typing import Any

from shvatka.api.shared.requests import MergeRequest, TimelineItem
from shvatka.core.models.enums import GameStatus
from shvatka.core.players.dto import TimelineItem as CoreTimelineItem


@dataclass
class AdminGameScenarioEdit:
    scenario: dict[str, Any]
    author_id: int | None = None
    """when set, the game is reassigned to this player before the scenario is saved"""


@dataclass
class AdminGameStatusChange:
    status: GameStatus
    """the status to move the game to; the game keeps everything else"""


@dataclass
class AdminChangeEmail:
    email: str
    verified: bool = False


@dataclass
class AdminChangeUsername:
    username: str


@dataclass
class AdminChangeTg:
    tg_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


@dataclass
class AdminNewCaptain:
    player_id: int


@dataclass
class AdminJoinTeam:
    player_id: int
    role: str | None = None
    emoji: str | None = None


@dataclass
class MergePlayersRequest(MergeRequest):
    timeline: list[TimelineItem] | None = None
    """manually built team history for the merged player; replaces both histories.
    Must not violate the waiver points of either player."""

    def core_timeline(self) -> list[CoreTimelineItem] | None:
        if self.timeline is None:
            return None
        return [item.to_core() for item in self.timeline]
