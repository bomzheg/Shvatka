from dataclasses import dataclass
from datetime import date


@dataclass
class ForumUser:
    db_id: int
    forum_id: int
    name: str
    registered: date
