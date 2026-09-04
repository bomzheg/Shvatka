from dataclasses import dataclass
from datetime import datetime

from shvatka.core.players.dto import TimelineItem as CoreTimelineItem


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
