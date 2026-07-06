"""Interactors used by the web UI to read player information.

They wrap the domain services from :mod:`shvatka.core.players.player` and operate
on internal domain models so the transport layer (api routes) stays thin.
"""

from dataclasses import dataclass

from shvatka.core.interfaces.dal.player import (
    PlayerByIdGetter,
    PlayerTeamChecker,
    TeamPlayerFullHistoryGetter,
)
from shvatka.core.models import dto
from shvatka.core.players.dto import PlayerMainInfo, PlayerStat
from shvatka.core.players.interfaces import (
    PlayedGamesByPlayerGetter,
    PlayerSearcher,
    PlayerWithStatGetter,
)
from shvatka.core.players.player import (
    get_full_team_player_or_none,
    get_player_with_stat,
    get_teams_history,
)


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
class GetPlayerStatInteractor:
    player_dao: PlayerWithStatGetter
    history_dao: TeamPlayerFullHistoryGetter
    played_games_dao: PlayedGamesByPlayerGetter

    async def __call__(self, player_id: int) -> PlayerStat:
        player = await get_player_with_stat(player_id, self.player_dao)
        team_history = await get_teams_history(player, self.history_dao)
        played_games = await self.played_games_dao.get_played_games(player)
        return PlayerStat(
            player=player,
            team_history=team_history,
            played_games=played_games,
        )


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
        can_be_author: bool | None = None,
    ) -> list[dto.Player]:
        return await self.dao.search_players(
            username=username,
            name=name,
            active=active,
            archive=archive,
            can_be_author=can_be_author,
        )
