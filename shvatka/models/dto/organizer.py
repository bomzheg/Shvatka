from dataclasses import dataclass

from .game import Game
from .player import Player


@dataclass(kw_only=True)
class Organizer:
    player: Player
    game: Game
    can_spy: bool
    can_see_log_keys: bool
    can_validate_waivers: bool
    deleted: bool


@dataclass(kw_only=True)
class SecondaryOrganizer(Organizer):
    id: int


@dataclass(kw_only=True)
class PrimaryOrganizer(Organizer):
    can_spy: bool = True
    can_see_log_keys: bool = True
    can_validate_waivers: bool = True
    deleted: bool = False
