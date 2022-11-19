from dataclasses import dataclass

from .player import Player
from .team_player import PlayerInTeam
from ..enums.played import Played


@dataclass
class VotedPlayer:
    player: Player
    pit: PlayerInTeam


@dataclass
class Vote:
    player: Player
    pit: PlayerInTeam
    vote: Played
