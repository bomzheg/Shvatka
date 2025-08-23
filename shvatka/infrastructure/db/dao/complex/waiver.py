import typing
from dataclasses import dataclass
from typing import Iterable, Sequence

from shvatka.core.interfaces.dal.waiver import WaiverApprover
from shvatka.core.waiver.adapters import WaiverVoteAdder, WaiverVoteGetter
from shvatka.core.models import dto
from shvatka.core.models.enums.played import Played

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class WaiverVoteAdderImpl(WaiverVoteAdder):
    dao: "HolderDao"

    async def is_excluded(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> bool:
        return await self.dao.waiver.is_excluded(game, player, team)

    async def add_player_vote(self, team_id: int, player_id: int, vote_var: str) -> None:
        return await self.dao.poll.add_player_vote(team_id, player_id, vote_var)

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.dao.team_player.get_team_player(player)


@dataclass
class WaiverVoteGetterImpl(WaiverVoteGetter):
    dao: "HolderDao"

    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        return await self.dao.poll.get_dict_player_vote(team_id)

    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        return await self.dao.player.get_by_ids_with_user_and_pit(ids)


@dataclass
class WaiverApproverImpl(WaiverApprover, WaiverVoteGetterImpl):
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
