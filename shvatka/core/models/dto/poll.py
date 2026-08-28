from dataclasses import dataclass

from shvatka.core.models.enums.played import Played

from .player import Player
from .team_player import TeamPlayer


@dataclass
class VotedPlayer:
    player: Player
    pit: TeamPlayer


@dataclass
class Vote:
    player: Player
    pit: TeamPlayer
    vote: Played
