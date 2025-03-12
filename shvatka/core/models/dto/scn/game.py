from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO, Sequence, Literal

from shvatka.core.models import enums
from shvatka.core.models.dto.export_stat import GameStat
from .level import LevelScenario
from shvatka.core.models.dto import hints


@dataclass
class GameScenario:
    name: str
    levels: list[LevelScenario]
    __model_version__: Literal[1]


@dataclass
class FullGameScenario(GameScenario):
    files: Sequence[hints.FileMeta]


@dataclass
class UploadedGameScenario(GameScenario):
    files: list[hints.UploadedFileMeta]


@dataclass
class ParsedGameScenario(GameScenario):
    files: list[hints.FileMetaLightweight]


@dataclass
class ParsedCompletedGameScenario(ParsedGameScenario):
    id: int
    start_at: datetime
    files_contents: dict[str, BinaryIO]
    stat: GameStat
    status: enums.GameStatus = enums.GameStatus.complete


@dataclass
class RawGameScenario:
    scn: dict
    files: dict[str, BinaryIO]
    stat: dict | None = None
