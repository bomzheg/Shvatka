from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO

from .file_content import FileMeta
from .level import LevelScenario
from ... import enums


@dataclass
class GameScenario:
    name: str
    levels: list[LevelScenario]


@dataclass
class FullGameScenario(GameScenario):
    files: list[FileMeta]


@dataclass
class ParsedCompletedGameScenario(FullGameScenario):
    id: int
    start_at: datetime
    status: enums.GameStatus = enums.GameStatus.complete


@dataclass
class RawGameScenario:
    scn: dict
    files: dict[str, BinaryIO]
