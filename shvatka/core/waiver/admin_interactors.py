"""Interactors backing the admin panel poll operations.

Unlike the organizer-facing poll readers, these are authorised at the transport
edge (superusers only), so they do not run organizer permission checks.
"""

from dataclasses import dataclass

from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.waiver.adapters import AdminPollReader, PollVoteRemover
from shvatka.core.waiver.services import get_vote_to_voted


@dataclass
class AdminPollReaderInteractor:
    dao: AdminPollReader

    async def __call__(self) -> dict[dto.Team, dict[Played, list[dto.VotedPlayer]]]:
        result: dict[dto.Team, dict[Played, list[dto.VotedPlayer]]] = {}
        for team_id in await self.dao.get_polled_teams():
            team = await self.dao.get_by_id(team_id)
            result[team] = await get_vote_to_voted(team, self.dao)
        return result


@dataclass
class AdminRemovePollVoteInteractor:
    dao: PollVoteRemover

    async def __call__(self, team_id: int, player_id: int) -> None:
        await self.dao.del_player_vote(team_id, player_id)
