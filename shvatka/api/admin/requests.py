from dataclasses import dataclass
from typing import Any

from shvatka.api.shared.requests import MergeRequest, TimelineItem
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.played import Played
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

    purge_runtime: bool = False
    """also erase what playing the game produced — level times, typed keys,
    events and timers. Only when a played game (``started``, ``finished``,
    ``complete``) is rewound to ``getting_waivers``, ``ready`` or
    ``underconstruction``; any other move is refused rather than half-obeyed.
    Waivers are never touched."""


@dataclass
class AdminResendLevel:
    team_id: int | None = None
    """the single team to resend to; ``null`` means every team of the game"""


@dataclass
class AdminAddWaiver:
    player_id: int
    played: Played = Played.yes
    """how the player takes part; ``yes`` is the roster, the rest are the ways out"""


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
