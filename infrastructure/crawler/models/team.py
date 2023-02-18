from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Team:
    name: str
    url: str
    id: int
    games: list[int]
    players: list[Player]


@dataclass
class Player:
    name: str
    role: str
    url: str
    games: list[int]
    registered_at: date
