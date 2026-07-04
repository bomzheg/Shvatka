"""Interactors backing the admin panel team operations.

Authorised at the transport edge is not enough: like the other admin
interactors these receive the configured superusers via DI and the acting user
via an ``IdentityProvider`` argument, and verify superuser rights themselves.
"""

from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.players.superuser import Superusers, check_is_superuser
from shvatka.core.services.team import merge_teams
from shvatka.core.teams.adapters import AdminTeamMerger
from shvatka.core.utils import exceptions
from shvatka.core.views.game import GameLogWriter


@dataclass
class AdminMergeTeamsInteractor:
    dao: AdminTeamMerger
    game_log: GameLogWriter
    superusers: Superusers

    async def __call__(
        self, identity: IdentityProvider, primary_id: int, secondary_id: int
    ) -> dto.Team:
        """Merge ``secondary`` team into ``primary``; ``secondary`` is deleted."""
        actor = await check_is_superuser(identity, self.superusers)
        if primary_id == secondary_id:
            raise exceptions.SHDataBreach(
                team_id=primary_id, notify_user="нельзя объединить команду с самой собой"
            )
        primary = await self.dao.get_by_id(primary_id)
        secondary = await self.dao.get_by_id(secondary_id)
        await merge_teams(actor, primary, secondary, self.game_log, self.dao)
        return await self.dao.get_by_id(primary_id)
