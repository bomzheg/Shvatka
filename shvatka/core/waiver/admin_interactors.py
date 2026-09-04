import logging
from collections.abc import Iterable
from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.players.player import get_checked_player_on_team
from shvatka.core.waiver import dto as waiver_dto
from shvatka.core.waiver.adapters import (
    AdminGameWaiversReader,
    AdminPollReader,
    AdminWaiverEditor,
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


@dataclass
class AdminAddWaiverInteractor:
    dao: AdminWaiverEditor

    async def __call__(
        self,
        identity: IdentityProvider,
        game_id: int,
        team_id: int,
        player_id: int,
        played: Played = Played.yes,
    ) -> waiver_dto.TeamWaivers:
        admin = await identity.get_superuser()
        game = await self.dao.get_game_by_id(game_id)
        team = await self.dao.get_team_by_id(team_id)
        player = await self.dao.get_player_by_id(player_id)
        await get_checked_player_on_team(player, team, self.dao)
        await self.dao.upsert(dto.Waiver(player=player, team=team, game=game, played=played))
        await self.dao.commit()
        logger.warning(
            "admin %s set waiver of player %s in team %s for game %s to %s",
            admin.id,
            player.id,
            team.id,
            game.id,
            played.name,
        )
        return waiver_dto.TeamWaivers(
            team=team, waivers=await self.dao.get_team_waivers(game, team)
        )


@dataclass
class AdminRemoveWaiverInteractor:
    dao: AdminWaiverEditor

    async def __call__(
        self, identity: IdentityProvider, game_id: int, team_id: int, player_id: int
    ) -> None:
        admin = await identity.get_superuser()
        game = await self.dao.get_game_by_id(game_id)
        team = await self.dao.get_team_by_id(team_id)
        player = await self.dao.get_player_by_id(player_id)
        await self.dao.delete(dto.WaiverQuery(player=player, team=team, game=game))
        await self.dao.commit()
        logger.warning(
            "admin %s removed waiver of player %s in team %s for game %s",
            admin.id,
            player.id,
            team.id,
            game.id,
        )
