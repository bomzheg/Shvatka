from dataclasses import dataclass
from typing import BinaryIO

from .file_content import FileMeta
from .level import LevelScenario


@dataclass
class GameScenario:
    name: str
    levels: list[LevelScenario]


@dataclass
class CompleteGameScenario(GameScenario):
    files: list[FileMeta]


@dataclass
class RawGameScenario:
    scn: dict
    files: dict[str, BinaryIO]
