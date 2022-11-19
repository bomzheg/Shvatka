from dataclasses import dataclass

from .player import Player
from .team_player import TeamPlayer
from ..enums.played import Played


@dataclass
class VotedPlayer:
    player: Player
    pit: TeamPlayer


@dataclass
class Vote:
    player: Player
    pit: TeamPlayer
    vote: Played
