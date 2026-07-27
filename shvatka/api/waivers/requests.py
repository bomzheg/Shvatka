from dataclasses import dataclass, field

from shvatka.core.models.enums.played import Played


@dataclass
class WaiverVote:
    player_id: int
    played: Played = Played.yes


@dataclass
class ReplaceWaivers:
    waivers: list[WaiverVote] = field(default_factory=list)
