from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from . import hints
from .player import Player
from .scn.level import LevelScenario
from .action.keys import BonusKey


@dataclass
class Level:
    db_id: int
    name_id: str
    author: Player
    scenario: LevelScenario
    game_id: int | None = None
    number_in_game: int | None = None

    def get_hint(self, hint_number: int) -> hints.TimeHint:
        return self.scenario.get_hint(hint_number)

    def get_hint_by_time(self, time: timedelta) -> hints.EnumeratedTimeHint:
        return self.scenario.get_hint_by_time(time)

    def is_last_hint(self, hint_number: int) -> bool:
        return self.scenario.is_last_hint(hint_number)

    def get_keys(self) -> set[str]:
        return self.scenario.get_keys()

    def get_bonus_keys(self) -> set[BonusKey]:
        return self.scenario.get_bonus_keys()

    def get_bonus_keys_texts(self) -> set[str]:
        return {key.text for key in self.scenario.get_bonus_keys()}

    def get_guids(self) -> list[str]:
        return self.scenario.get_guids()

    @property
    def hints_count(self) -> int:
        return self.scenario.hints_count

    def get_hints_for_timedelta(self, delta: timedelta) -> list[hints.TimeHint]:
        return self.scenario.get_hints_for_timedelta(delta)

    def is_routed(self) -> bool:
        return self.scenario.is_routed()
