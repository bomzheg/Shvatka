"""Interactors used by the web UI to read and manage teams.

They wrap the domain services from :mod:`shvatka.core.services.team` and
:mod:`shvatka.core.players.player` and operate on internal domain models so the
transport layer (api routes) stays thin.
"""

import contextlib
from dataclasses import dataclass
from typing import Sequence

from shvatka.core.interfaces.dal.player import PlayerByIdGetter, TeamLeaver, TeamPlayersGetter
from shvatka.core.interfaces.dal.team import TeamByIdGetter, TeamsGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto, enums
from shvatka.core.players.player import (
    check_can_manage_players,
    get_full_team_player,
    get_team_players,
    join_team,
    leave,
)
from shvatka.core.services.team import (
    change_team_desc,
    get_team_by_id,
    get_teams,
    rename_team,
)
from shvatka.core.teams.adapters import TeamEditor, TeamPlayerAdder, TeamPlayerUpdater
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE
from shvatka.core.utils.exceptions import PlayerRestoredInTeam


@dataclass
class TeamsListInteractor:
    dao: TeamsGetter

    async def __call__(self, active: bool = True, archive: bool = False) -> list[dto.Team]:
        return await get_teams(self.dao, active=active, archive=archive)


@dataclass
class GetTeamInteractor:
    dao: TeamByIdGetter

    async def __call__(self, team_id: int) -> dto.Team:
        return await get_team_by_id(team_id, self.dao)


@dataclass
class TeamPlayersInteractor:
    team_dao: TeamByIdGetter
    players_dao: TeamPlayersGetter

    async def __call__(self, team_id: int) -> Sequence[dto.FullTeamPlayer]:
        team = await get_team_by_id(team_id, self.team_dao)
        return await get_team_players(team, self.players_dao)


@dataclass
class AddPlayerToMyTeamInteractor:
    dao: TeamPlayerAdder
    player_dao: PlayerByIdGetter

    async def __call__(
        self,
        player_id: int,
        identity: IdentityProvider,
        role: str | None = None,
        emoji: str | None = None,
    ) -> dto.FullTeamPlayer:
        manager = await identity.get_required_player()
        team = await identity.get_required_team()
        player = await self.player_dao.get_by_id(player_id)
        with contextlib.suppress(PlayerRestoredInTeam):
            await join_team(player, team, manager, self.dao, role=role or DEFAULT_ROLE)
        if emoji is not None:
            team_player = await self.dao.get_team_player(player)
            await self.dao.change_emoji(team_player, emoji)
            await self.dao.commit()
        return await get_full_team_player(player, team, self.dao)


@dataclass
class RemovePlayerFromTeamInteractor:
    dao: TeamLeaver
    player_dao: PlayerByIdGetter

    async def __call__(self, player_id: int, identity: IdentityProvider) -> None:
        remover = await identity.get_required_player()
        player = await self.player_dao.get_by_id(player_id)
        await leave(player, remover, self.dao)


@dataclass
class UpdateTeamPlayerInteractor:
    dao: TeamPlayerUpdater
    team_dao: TeamByIdGetter
    player_dao: PlayerByIdGetter

    async def __call__(
        self,
        team_id: int,
        player_id: int,
        identity: IdentityProvider,
        role: str | None = None,
        emoji: str | None = None,
        permissions: dict[str, bool] | None = None,
    ) -> dto.FullTeamPlayer:
        manager = await identity.get_required_player()
        team = await get_team_by_id(team_id, self.team_dao)
        manager_team_player = await get_full_team_player(manager, team, self.dao)
        check_can_manage_players(manager_team_player)
        player = await self.player_dao.get_by_id(player_id)
        # raises PlayerNotInTeam if the player is not in this team (or already left)
        target = await get_full_team_player(player, team, self.dao)
        if role is not None:
            await self.dao.change_role(target, role)
        if emoji is not None:
            await self.dao.change_emoji(target, emoji)
        for permission_name, value in (permissions or {}).items():
            permission = enums.TeamPlayerPermission[permission_name]
            if target.permissions[permission] != value:
                await self.dao.flip_permission(target, permission)
        await self.dao.commit()
        return await get_full_team_player(player, team, self.dao)


@dataclass
class EditTeamInteractor:
    dao: TeamEditor

    async def __call__(
        self,
        team_id: int,
        identity: IdentityProvider,
        name: str | None = None,
        description: str | None = None,
    ) -> dto.Team:
        captain = await identity.get_required_full_team_player()
        team = await get_team_by_id(team_id, self.dao)
        if name is not None:
            await rename_team(team, captain, name, self.dao)
        if description is not None:
            await change_team_desc(team, captain, description, self.dao)
        return await get_team_by_id(team_id, self.dao)
