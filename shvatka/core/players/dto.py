from dataclasses import dataclass

from shvatka.core.models import dto


@dataclass(frozen=True, slots=True)
class PlayerMainInfo:
    """Main info about a player together with their current team membership."""

    player: dto.Player
    team_player: dto.FullTeamPlayer | None


@dataclass(frozen=True, slots=True)
class PlayerStat:
    """Aggregated player statistics for the web UI.

    Includes the player together with key counters, the full history of team
    memberships and the list of games the player took part in.
    """

    player: dto.PlayerWithStat
    team_history: list[dto.FullTeamPlayer]
    played_games: list[dto.Game]
