from dataclasses import dataclass

from .player import Player
from .player_in_team import PlayerInTeam


@dataclass
class VotedPlayer:
    player: Player
    pit: PlayerInTeam
