from dataclasses import dataclass

from app.models.dto import Player, Team, Game
from app.models.enums.played import Played


@dataclass
class Waiver:
    player: Player
    team: Team
    game: Game
    played: Played | None = None
