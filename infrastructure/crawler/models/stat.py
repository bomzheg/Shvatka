from dataclasses import dataclass
from datetime import datetime


@dataclass
class LevelTime:
    number: int
    at: datetime | None


@dataclass
class Key:
    level: int
    player: str
    at: datetime
    value: str


@dataclass
class GameStat:
    results: dict[str, list[LevelTime]]
    keys: dict[str, list[Key]]
