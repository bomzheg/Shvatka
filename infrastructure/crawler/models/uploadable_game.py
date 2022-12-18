from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class LevelPuzzle:
    level_number: int
    hint_number: int
    "для уровня - тут всегда 0"
    next_hint_time: int
    "время выхода следующей(!) подсказки в минутах. Если это последняя - ставим 0"
    text: str
    key: str
    brain_key: str


@dataclass
class Hint:
    level_number: int
    hint_number: int
    next_hint_time: int
    "время выхода следующей(!) подсказки в минутах. Если последняя - ставим 0"
    text: str


class LevelForUpload(NamedTuple):
    puzzle: LevelPuzzle
    hints: list[Hint]


GameForUpload = list[LevelForUpload]
