from dataclasses import dataclass

from .level import Level
from .organizer import Organizer


@dataclass
class LevelTestSuite:
    level: Level
    tester: Organizer
