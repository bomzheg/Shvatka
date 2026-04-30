from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models.dto import action


@dataclass
class GameEvent:
    id: int
    team_id: int
    level_time_id: int
    at: datetime
    effects: action.Effects
