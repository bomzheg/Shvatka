"""Interactors backing the admin panel team operations.

Each interactor takes the acting user via an ``IdentityProvider`` argument and
authorises through ``identity.get_superuser()`` before performing the operation.
"""

import contextlib
import logging
from dataclasses import dataclass

from shvatka.core.interfaces.dal.player import PlayerByIdGetter, TeamLeaver
from shvatka.core.interfaces.dal.team import TeamByIdGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.players.player import (
    force_join_team,
    force_leave,
    get_full_team_player,
)
from shvatka.core.services.team import change_captain, get_team_by_id, merge_teams
from shvatka.core.teams.adapters import (
    AdminTeamMerger,
    TeamCaptainSetter,
    TeamPlayerAdder,
)
from shvatka.core.utils import exceptions
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE
from shvatka.core.utils.exceptions import PlayerRestoredInTeam
from shvatka.core.views.game import GameLogWriter
from shvatka.core.views.team import TeamNotifier

logger = logging.getLogger(__name__)


@dataclass
class AdminMergeTeamsInteractor:
    dao: AdminTeamMerger
    game_log: GameLogWriter

    async def __call__(
        self, identity: IdentityProvider, primary_id: int, secondary_id: int
    ) -> dto.Team:
        """Merge ``secondary`` team into ``primary``; ``secondary`` is deleted."""
        actor = await identity.get_superuser()
        logger.warning("admin %s merges team %s into %s", actor.id, secondary_id, primary_id)
        if primary_id == secondary_id:
            raise exceptions.MergeError(
                team_id=primary_id, notify_user="нельзя объединить команду с самой собой"
            )
        primary = await self.dao.get_by_id(primary_id)
        secondary = await self.dao.get_by_id(secondary_id)
        await merge_teams(actor, primary, secondary, self.game_log, self.dao)
        return await self.dao.get_by_id(primary_id)


@dataclass
class AdminChangeTeamCaptainInteractor:
    """Give a team another captain, over the head of the current one.

    The way out of the deadlock the captain themselves can't solve: a captain
    who is gone, or one who left without handing the team over.
    """

    dao: TeamCaptainSetter
    notifier: TeamNotifier

    async def __call__(self, identity: IdentityProvider, team_id: int, player_id: int) -> dto.Team:
        admin = await identity.get_superuser()
        team = await get_team_by_id(team_id, self.dao)
        logger.warning(
            "admin %s makes player %s the captain of team %s", admin.id, player_id, team_id
        )
        return await change_captain(team, admin, player_id, self.dao, self.notifier)


@dataclass
class AdminAddPlayerToTeamInteractor:
    """Put a player into a team without the team's permissions applying."""

    dao: TeamPlayerAdder
    team_dao: TeamByIdGetter
    player_dao: PlayerByIdGetter
    notifier: TeamNotifier

    async def __call__(
        self,
        identity: IdentityProvider,
        team_id: int,
        player_id: int,
        role: str | None = None,
        emoji: str | None = None,
    ) -> dto.FullTeamPlayer:
        admin = await identity.get_superuser()
        team = await self.team_dao.get_by_id(team_id)
        player = await self.player_dao.get_by_id(player_id)
        logger.warning("admin %s adds player %s to team %s", admin.id, player_id, team_id)
        with contextlib.suppress(PlayerRestoredInTeam):
            await force_join_team(
                player,
                team,
                admin,
                self.dao,
                notifier=self.notifier,
                role=role or DEFAULT_ROLE,
            )
        if emoji is not None:
            team_player = await self.dao.get_team_player(player)
            await self.dao.change_emoji(team_player, emoji)
            await self.dao.commit()
        return await get_full_team_player(player, team, self.dao)


@dataclass
class AdminRemovePlayerFromTeamInteractor:
    """Take a player out of whichever team they are in."""

    dao: TeamLeaver
    player_dao: PlayerByIdGetter
    notifier: TeamNotifier

    async def __call__(self, identity: IdentityProvider, player_id: int) -> None:
        admin = await identity.get_superuser()
        player = await self.player_dao.get_by_id(player_id)
        logger.warning("admin %s removes player %s from their team", admin.id, player_id)
        await force_leave(player, admin, self.dao, notifier=self.notifier)
