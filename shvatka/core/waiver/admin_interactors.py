"""Interactors backing the admin panel poll operations.

Each interactor receives the configured superusers via DI and the acting user
via an ``IdentityProvider`` argument, and verifies superuser rights itself
before reading or mutating poll data.
"""

from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.players.superuser import Superusers, check_is_superuser
from shvatka.core.waiver.adapters import AdminPollReader, PollVoteRemover
from shvatka.core.waiver.services import get_vote_to_voted


@dataclass
class AdminPollReaderInteractor:
    dao: AdminPollReader
    superusers: Superusers

    async def __call__(
        self, identity: IdentityProvider
    ) -> dict[dto.Team, dict[Played, list[dto.VotedPlayer]]]:
        await check_is_superuser(identity, self.superusers)
        result: dict[dto.Team, dict[Played, list[dto.VotedPlayer]]] = {}
        for team_id in await self.dao.get_polled_teams():
            team = await self.dao.get_by_id(team_id)
            result[team] = await get_vote_to_voted(team, self.dao)
        return result


@dataclass
class AdminRemovePollVoteInteractor:
    dao: PollVoteRemover
    superusers: Superusers

    async def __call__(self, identity: IdentityProvider, team_id: int, player_id: int) -> None:
        await check_is_superuser(identity, self.superusers)
        await self.dao.del_player_vote(team_id, player_id)
