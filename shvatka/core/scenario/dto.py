from dataclasses import dataclass

from shvatka.core.models.dto import action


@dataclass
class Key:
    keys: set[action.SHKey]
    description: str


@dataclass
class LevelKeys:
    level_number: int
    level_name_id: str
    keys: list[Key]


@dataclass
class Transitions:
    game_name: str
    levels: list[tuple[int, str]]
    transitions: list[tuple[str, str]]
