from dataclasses import dataclass

from shvatka.core.models import dto


@dataclass(frozen=True, slots=True)
class PlayerMainInfo:
    """Main info about a player together with their current team membership."""

    player: dto.Player
    team_player: dto.FullTeamPlayer | None
