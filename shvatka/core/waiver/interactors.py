from shvatka.core.interfaces.dal.waiver import WaiverVoteGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.services.waiver import check_allow_approve_waivers, get_vote_to_voted
from shvatka.core.utils import exceptions


class WaiversReaderInteractor:
    def __init__(self, dao: WaiverVoteGetter) -> None:
        self.dao = dao

    async def __call__(
        self, game_id: int, identity: IdentityProvider
    ) -> dict[Played, list[dto.VotedPlayer]]:
        team_player = await identity.get_full_team_player()
        if team_player is None:
            raise exceptions.PlayerNotInTeam
        check_allow_approve_waivers(team_player)
        team = team_player.team
        return await get_vote_to_voted(team, self.dao)
