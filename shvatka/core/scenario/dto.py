from dataclasses import dataclass
from typing import NamedTuple

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


class ShortLevel(NamedTuple):
    level_number: int
    level_name_id: str


class Transition(NamedTuple):
    from_: str
    to: str
    condition: str


@dataclass
class Transitions:
    game_name: str
    levels: list[ShortLevel]
    levels_conditions: dict[str, list[tuple[str, bool]]]
    forward_transitions: list[Transition]
    routed_transitions: list[Transition]
