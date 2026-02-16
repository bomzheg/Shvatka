from dataclasses import dataclass

from shvatka.core.models import dto


@dataclass
class Timer:
    id: int
    level_time_id: int
    event: dto.GameEvent
