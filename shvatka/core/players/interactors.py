"""Interactors used by the web UI to read player information.

They wrap the domain services from :mod:`shvatka.core.players.player` and operate
on internal domain models so the transport layer (api routes) stays thin.
"""

from dataclasses import dataclass

from shvatka.core.interfaces.dal.player import PlayerByIdGetter, PlayerTeamChecker
from shvatka.core.models import dto
from shvatka.core.players.interfaces import PlayerSearcher
from shvatka.core.players.player import get_full_team_player_or_none


@dataclass(frozen=True, slots=True)
class PlayerMainInfo:
    """Main info about a player together with their current team membership."""

    player: dto.Player
    team_player: dto.FullTeamPlayer | None


@dataclass
class GetPlayerInteractor:
    player_dao: PlayerByIdGetter
    team_player_dao: PlayerTeamChecker

    async def __call__(self, player_id: int) -> PlayerMainInfo:
        player = await self.player_dao.get_by_id(player_id)
        team = await self.team_player_dao.get_team(player)
        team_player = await get_full_team_player_or_none(player, team, self.team_player_dao)
        return PlayerMainInfo(player=player, team_player=team_player)


@dataclass
class SearchPlayersInteractor:
    dao: PlayerSearcher

    async def __call__(
        self,
        *,
        username: str | None = None,
        name: str | None = None,
        active: bool = True,
        archive: bool = False,
    ) -> list[dto.Player]:
        return await self.dao.search_players(
            username=username,
            name=name,
            active=active,
            archive=archive,
        )
