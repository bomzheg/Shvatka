from dataclasses import dataclass
from datetime import datetime

from shvatka.models import dto


@dataclass(frozen=True)
class KeyTime:
    text: str
    is_correct: bool
    is_duplicate: bool
    at: datetime
    level_number: int
    player: dto.Player
