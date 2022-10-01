from __future__ import annotations

from dataclasses import dataclass

from db import models
from shvatka.models.dto.scn.level import LevelScenario
from .player import Player


@dataclass
class Level:
    db_id: int
    name_id: str
    author: Player
    scenario: LevelScenario
    game_id: int | None = None
    number_in_game: int | None = None

    @classmethod
    def from_db(cls, level: models.Level, author: Player) -> Level:
        return cls(
            db_id=level.id,
            name_id=level.name_id,
            author=author,
            scenario=level.scenario,
            game_id=level.game_id,
            number_in_game=level.number_in_game,
        )
