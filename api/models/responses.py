from dataclasses import dataclass
from datetime import datetime

from shvatka.models import dto
from shvatka.models.dto import Player
from shvatka.models.enums import GameStatus


@dataclass
class Game:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None

    @classmethod
    def from_core(cls, core: dto.Game):
        return cls(
            id=core.id,
            author=core.author,
            name=core.name,
            status=core.status,
            start_at=core.start_at,
        )
