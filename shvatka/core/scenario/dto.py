from dataclasses import dataclass
from datetime import datetime
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


@dataclass
class KeysSheet:
    """Keys of a game prepared to be printed and cut into slips for the orgs.

    Nothing but the keys themselves — every slip is signed with the name and the
    date of the game, so a slip found later still says where it is from.
    """

    game_name: str
    game_date: datetime | None
    keys: list[action.SHKey]
    """Every key of the game once, in the order levels are played."""


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
