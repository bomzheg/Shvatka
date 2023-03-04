from dataclasses import dataclass

from src.core.models.dto import Player, Team, Game
from src.core.models.enums.played import Played


@dataclass
class Waiver:
    player: Player
    team: Team
    game: Game
    played: Played | None = None
