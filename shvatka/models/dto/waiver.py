from dataclasses import dataclass

from shvatka.models.dto import Player, Team, Game
from shvatka.models.enums.played import Played


@dataclass
class Waiver:
    player: Player
    team: Team
    game: Game
    played: Played | None = None
