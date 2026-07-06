"""Interactors backing the admin panel poll and waiver operations.

Each interactor takes the acting user via an ``IdentityProvider`` argument and
authorises through ``identity.get_superuser()`` before reading or mutating data.
"""

import logging
from dataclasses import dataclass
from typing import Iterable

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.waiver.adapters import (
    AdminGameWaiversReader,
    AdminPollReader,
    PollVoteRemover,
)
from shvatka.core.waiver.services import get_all_played, get_vote_to_voted

logger = logging.getLogger(__name__)


@dataclass
class AdminPollReaderInteractor:
    dao: AdminPollReader

    async def __call__(
        self, identity: IdentityProvider
    ) -> dict[dto.Team, dict[Played, list[dto.VotedPlayer]]]:
        admin = await identity.get_superuser()
        logger.warning("admin %s read the poll", admin.id)
        result: dict[dto.Team, dict[Played, list[dto.VotedPlayer]]] = {}
        for team_id in await self.dao.get_polled_teams():
            team = await self.dao.get_by_id(team_id)
            result[team] = await get_vote_to_voted(team, self.dao)
        return result


@dataclass
class AdminRemovePollVoteInteractor:
    dao: PollVoteRemover

    async def __call__(self, identity: IdentityProvider, team_id: int, player_id: int) -> None:
        admin = await identity.get_superuser()
        logger.warning(
            "admin %s removed poll vote of player %s in team %s", admin.id, player_id, team_id
        )
        await self.dao.del_player_vote(team_id, player_id)


@dataclass
class AdminGameWaiversReaderInteractor:
    dao: AdminGameWaiversReader

    async def __call__(
        self, identity: IdentityProvider, game_id: int
    ) -> dict[dto.Team, Iterable[dto.VotedPlayer]]:
        admin = await identity.get_superuser()
        logger.warning("admin %s read waivers of game %s", admin.id, game_id)
        game = await self.dao.get_by_id(game_id)  # raises GameNotFound if absent
        return await get_all_played(game, self.dao)
