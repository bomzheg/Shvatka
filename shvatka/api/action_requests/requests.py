from dataclasses import dataclass

from shvatka.api.shared.requests import TimelineItem
from shvatka.core.players.dto import TimelineItem as CoreTimelineItem


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


@dataclass
class PromotionInvite:
    player_id: int


@dataclass
class AcceptRequest:
    timeline: list[TimelineItem] | None = None
    """only for player merge requests: manually built team history replacing
    both players' histories when they are not compatible."""

    def core_timeline(self) -> list[CoreTimelineItem] | None:
        if self.timeline is None:
            return None
        return [item.to_core() for item in self.timeline]
