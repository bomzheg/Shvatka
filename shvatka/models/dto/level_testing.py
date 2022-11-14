from dataclasses import dataclass

from shvatka.models.dto import Level, Organizer


@dataclass
class LevelTestSuite:
    level: Level
    tester: Organizer
