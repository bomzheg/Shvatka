from dataclasses import dataclass

from shvatka.core.models.dto import Game, Player, Team
from shvatka.core.models.enums.played import Played


@dataclass
class Waiver:
    player: Player
    team: Team
    game: Game
    played: Played


@dataclass
class WaiverQuery:
    player: Player
    team: Team
    game: Game
