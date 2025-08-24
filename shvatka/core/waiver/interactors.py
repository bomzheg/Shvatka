from typing import Iterable

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.waiver import GameWaiversGetter
from shvatka.core.services.organizers import get_by_player, check_can_check_waivers
from shvatka.core.services.team import get_team_by_id
from shvatka.core.waiver.adapters import WaiverVoteAdder, WaiverVoteGetter, PollDraftsReader
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.waiver.services import (
    check_allow_approve_waivers,
    get_vote_to_voted,
    add_vote,
    get_all_played,
)
from shvatka.core.utils import exceptions


class WaiverCompleteReaderInteractor:
    def __init__(self, dao: GameWaiversGetter) -> None:
        self.dao = dao

    async def __call__(self, game: dto.Game) -> dict[dto.Team, Iterable[dto.VotedPlayer]]:
        return await get_all_played(game, self.dao)


class WaiversReaderInteractor:
    def __init__(self, dao: WaiverVoteGetter) -> None:
        self.dao = dao

    async def __call__(
        self, game_id: int, identity: IdentityProvider
    ) -> dict[Played, list[dto.VotedPlayer]]:
        team_player = await identity.get_full_team_player()
        if team_player is None:
            raise exceptions.PlayerNotInTeam(
                player=await identity.get_player(), team=await identity.get_team()
            )
        check_allow_approve_waivers(team_player)
        team = team_player.team
        return await get_vote_to_voted(team, self.dao)


class AddWaiverVoteInteractor:
    def __init__(self, dao: WaiverVoteAdder, current_game: CurrentGameProvider) -> None:
        self.dao = dao
        self.current_game = current_game

    async def __call__(self, identity: IdentityProvider, vote: Played) -> None:
        player = await identity.get_required_player()
        team = await identity.get_team()
        if team is None:
            raise exceptions.PlayerNotInTeam(player=player, team=team)
        game = await self.current_game.get_required_game()
        await add_vote(
            game=game,
            team=team,
            player=player,
            vote=vote,
            dao=self.dao,
        )


class WaiverDraftReaderInteractor:
    def __init__(
        self,
        dao: PollDraftsReader,
        current_game: CurrentGameProvider,
    ) -> None:
        self.dao = dao
        self.current_game = current_game

    async def __call__(self, identity: IdentityProvider) -> dict[dto.Team, dict[Played, int]]:
        player = await identity.get_required_player()
        game = await self.current_game.get_required_game()
        org = await get_by_player(game=game, player=player, dao=self.dao)
        check_can_check_waivers(org)
        team_ids = await self.dao.get_polled_teams()
        results: dict[dto.Team, dict[Played, int]] = {}
        for team_id in team_ids:
            team = await get_team_by_id(team_id, self.dao)
            results[team] = {
                played: len(players)
                for played, players in (await get_vote_to_voted(team, self.dao)).items()
            }
        return results
