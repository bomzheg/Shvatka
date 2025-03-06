from dataclasses import dataclass
from datetime import date


@dataclass
class ForumUser:
    db_id: int
    forum_id: int | None
    name: str
    registered: date | None
    player_id: int

    @property
    def name_mention(self) -> str:
        return self.name or (f"forum-user-{self.forum_id}" if self.forum_id else str(self.db_id))
