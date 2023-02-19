from __future__ import annotations

from dataclasses import dataclass
from datetime import date


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
