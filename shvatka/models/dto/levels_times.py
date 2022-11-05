from dataclasses import dataclass
from datetime import datetime

from .game import Game
from .team import Team


@dataclass
class LevelTime:
    id: int
    game: Game
    team: Team
    level_number: int
    start_at: datetime


@dataclass
class GameStat:
    level_times: dict[Team, list[LevelTime]]
