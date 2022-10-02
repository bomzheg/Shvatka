from dataclasses import dataclass

from .game import Game
from .player import Player


@dataclass
class Organizer:
    id: int
    player: Player
    game: Game
    can_spy: bool
    can_see_log_keys: bool
    can_validate_waivers: bool
    deleted: bool
