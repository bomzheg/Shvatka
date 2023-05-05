from dataclasses import dataclass, field
from datetime import datetime

from asyncpg.pgproto.pgproto import timedelta

from .level import Level
from .organizer import Organizer


@dataclass
class LevelTestSuite:
    level: Level
    tester: Organizer


@dataclass
class SimpleKey:
    text: str
    at: datetime
    is_correct: bool


@dataclass
class LevelTestProtocol:
    start: datetime | None = None
    stop: datetime | None = None


@dataclass
class LevelTestBucket:
    protocol: LevelTestProtocol = field(default_factory=LevelTestProtocol)
    correct_typed: set[str] = field(default_factory=set)
    all_typed: list[SimpleKey] = field(default_factory=list)


@dataclass
class LevelTestingResult:
    full_data: LevelTestBucket
    td: timedelta
