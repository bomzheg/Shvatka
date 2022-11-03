from dataclasses import dataclass
from datetime import datetime

from shvatka.models.dto import Game, Team


@dataclass
class LevelTime:
    id: int
    game: Game
    team: Team
    level_number: int
    start_at: datetime
