from __future__ import annotations

from dataclasses import dataclass

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

