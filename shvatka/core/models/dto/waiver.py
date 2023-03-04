from dataclasses import dataclass

from shvatka.core.models.dto import Player, Team, Game
from shvatka.core.models.enums.played import Played


@dataclass
class Waiver:
    player: Player
    team: Team
    game: Game
    played: Played | None = None
