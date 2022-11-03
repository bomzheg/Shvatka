from dataclasses import dataclass

from .file_content import FileContent
from .level import LevelScenario


@dataclass
class GameScenario:
    name: str
    levels: list[LevelScenario]


@dataclass
class UploadedGameScenario(GameScenario):
    files: list[FileContent]
