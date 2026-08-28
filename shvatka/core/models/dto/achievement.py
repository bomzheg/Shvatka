from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models import enums

from .player import Player


@dataclass
class Achievement:
    player: Player
    name: enums.Achievement
    first: bool
    at: datetime | None = None
