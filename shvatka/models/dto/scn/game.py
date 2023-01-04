from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO

from shvatka.models import enums
from . import UploadedFileMeta
from .file_content import FileMeta
from .level import LevelScenario


@dataclass
class GameScenario:
    name: str
    levels: list[LevelScenario]


@dataclass
class FullGameScenario(GameScenario):
    files: list[FileMeta]


@dataclass
class UploadedGameScenario(GameScenario):
    files: list[UploadedFileMeta]


@dataclass
class ParsedCompletedGameScenario(FullGameScenario):
    id: int
    start_at: datetime
    files_contents: dict[str, BinaryIO]
    status: enums.GameStatus = enums.GameStatus.complete


@dataclass
class RawGameScenario:
    scn: dict
    files: dict[str, BinaryIO]
