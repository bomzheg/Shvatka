from dataclasses import dataclass


@dataclass
class ForumTeam:
    id: int
    forum_id: int
    name: str
    url: str
