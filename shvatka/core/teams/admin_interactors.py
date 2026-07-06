"""Interactors backing the admin panel team operations.

Each interactor takes the acting user via an ``IdentityProvider`` argument and
authorises through ``identity.get_superuser()`` before performing the operation.
"""

from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services.team import merge_teams
from shvatka.core.teams.adapters import AdminTeamMerger
from shvatka.core.utils import exceptions
from shvatka.core.views.game import GameLogWriter


@dataclass
class AdminMergeTeamsInteractor:
    dao: AdminTeamMerger
    game_log: GameLogWriter

    async def __call__(
        self, identity: IdentityProvider, primary_id: int, secondary_id: int
    ) -> dto.Team:
        """Merge ``secondary`` team into ``primary``; ``secondary`` is deleted."""
        actor = await identity.get_superuser()
        if primary_id == secondary_id:
            raise exceptions.MergeError(
                team_id=primary_id, notify_user="нельзя объединить команду с самой собой"
            )
        primary = await self.dao.get_by_id(primary_id)
        secondary = await self.dao.get_by_id(secondary_id)
        await merge_teams(actor, primary, secondary, self.game_log, self.dao)
        return await self.dao.get_by_id(primary_id)
