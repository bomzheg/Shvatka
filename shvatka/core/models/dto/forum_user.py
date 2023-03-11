from dataclasses import dataclass
from datetime import date


@dataclass
class ForumUser:
    db_id: int
    forum_id: int
    name: str
    registered: date

    @property
    def name_mention(self) -> str:
        return self.name or f"forum-user-{self.forum_id}" if self.forum_id else self.db_id
