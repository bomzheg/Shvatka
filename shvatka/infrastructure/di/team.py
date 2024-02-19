from dishka import Provider, Scope, provide

from shvatka.core.models import dto
from shvatka.core.services.player import get_my_team
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao


class TeamProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_team_provider(
        self,
        dao: HolderDao,
        player: dto.Player,
    ) -> dto.Team:
        team = await get_my_team(player, dao.team_player)
        if team is None:
            raise exceptions.PlayerNotInTeam(player=player)
        return team
