from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus


@dataclass
class Player:
    id: int
    can_be_author: bool

    @classmethod
    def from_core(cls, core: dto.Player):
        return cls(
            id=core.id,
            can_be_author=core.can_be_author,
        )


@dataclass
class Team:
    id: int
    name: str
    captain: Player | None
    description: str | None

    @classmethod
    def from_core(cls, core: dto.Team):
        return cls(
            id=core.id,
            name=core.name,
            captain=Player.from_core(core.captain) if core.captain else None,
            description=core.description,
        )


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
            author=Player.from_core(core.author),
            name=core.name,
            status=core.status,
            start_at=core.start_at,
        )
