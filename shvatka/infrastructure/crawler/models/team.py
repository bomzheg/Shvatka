from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class ParsedTeam:
    name: str
    url: str
    id: int
    games: list[int]
    players: list[ParsedPlayer]


@dataclass(frozen=True)
class ParsedPlayer:
    name: str
    role: str
    url: str
    games: list[int]
    registered_at: date
    forum_id: int | None

    def __hash__(self):
        return hash(self.forum_id)

    def __eq__(self, other: Any):
        if not isinstance(other, ParsedPlayer):
            return NotImplemented
        return self.forum_id == other.forum_id
