import typing
from dataclasses import dataclass
from typing import Sequence

from shvatka.core.interfaces.dal.waiver import WaiverApprover
from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.waiver.adapters import WaiverVoteGetter

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class WaiverApproverImpl(WaiverApprover, WaiverVoteGetter):
    dao: "HolderDao"

    async def upsert(self, waiver: dto.Waiver) -> None:
        return await self.dao.waiver.upsert(waiver)

    async def commit(self) -> None:
        return await self.dao.waiver.commit()

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.dao.team_player.get_team_player(player)

    async def get_players(self, team: dto.Team) -> Sequence[dto.FullTeamPlayer]:
        return await self.dao.team_player.get_players(team)

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        return await self.dao.poll.del_player_vote(team_id, player_id)

    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        return await self.dao.poll.get_dict_player_vote(team_id)

    async def get_by_ids_with_user_and_pit(
        self, ids: typing.Iterable[int]
    ) -> list[dto.VotedPlayer]:
        return await self.dao.player.get_by_ids_with_user_and_pit(ids)
