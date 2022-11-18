from __future__ import annotations

from dataclasses import dataclass

from shvatka.models.dto.scn.level import LevelScenario
from .player import Player
from .scn.time_hint import TimeHint


@dataclass
class Level:
    db_id: int
    name_id: str
    author: Player
    scenario: LevelScenario
    game_id: int | None = None
    number_in_game: int | None = None

    def get_hint(self, hint_number: int) -> TimeHint:
        return self.scenario.get_hint(hint_number)

    def is_last_hint(self, hint_number: int) -> bool:
        return self.scenario.is_last_hint(hint_number)

    def get_keys(self):
        return self.scenario.get_keys()

    def get_guids(self) -> list[str]:
        return self.scenario.get_guids()

    @property
    def hints_count(self) -> int:
        return self.scenario.hints_count
