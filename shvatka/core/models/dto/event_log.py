from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models import dto
from shvatka.core.models.dto import action


@dataclass
class GameEvent:
    team: dto.Team
    level_number: int
    level_team_id: int
    at: datetime
    effects: action.Effects
