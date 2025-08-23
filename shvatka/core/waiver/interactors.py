from shvatka.core.waiver.adapters import WaiverVoteAdder, WaiverVoteGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.services.waiver import check_allow_approve_waivers, get_vote_to_voted, add_vote
from shvatka.core.utils import exceptions


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
    def __init__(self, dao: WaiverVoteAdder) -> None:
        self.dao = dao

    async def __call__(self, game: dto.Game, identity: IdentityProvider, vote: Played) -> None:
        team = await identity.get_team()
        player = await identity.get_player()
        if team is None or player is None:
            raise exceptions.PlayerNotInTeam(player=player, team=team)
        await add_vote(
            game=game,
            team=team,
            player=player,
            vote=vote,
            dao=self.dao,
        )
