from dataclasses import dataclass
from typing import Iterable, Sequence

from shvatka.core.interfaces.dal.waiver import WaiverVoteAdder, WaiverVoteGetter, WaiverApprover
from shvatka.core.models import dto
from shvatka.core.models.enums.played import Played
from shvatka.infrastructure.db.dao import PollDao, WaiverDao, PlayerDao, TeamPlayerDao


@dataclass
class WaiverVoteAdderImpl(WaiverVoteAdder):
    poll: PollDao
    waiver: WaiverDao
    team_player: TeamPlayerDao

    async def is_excluded(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> bool:
        return await self.waiver.is_excluded(game, player, team)

    async def add_player_vote(self, team_id: int, player_id: int, vote_var: str) -> None:
        return await self.poll.add_player_vote(team_id, player_id, vote_var)

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.team_player.get_team_player(player)


@dataclass
class WaiverVoteGetterImpl(WaiverVoteGetter):
    poll: PollDao
    player: PlayerDao

    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        return await self.poll.get_dict_player_vote(team_id)

    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        return await self.player.get_by_ids_with_user_and_pit(ids)


@dataclass
class WaiverApproverImpl(WaiverApprover, WaiverVoteGetterImpl):
    waiver: WaiverDao
    team_player: TeamPlayerDao

    async def upsert(self, waiver: dto.Waiver) -> None:
        return await self.waiver.upsert(waiver)

    async def commit(self) -> None:
        return await self.waiver.commit()

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.team_player.get_team_player(player)

    async def get_players(self, team: dto.Team) -> Sequence[dto.FullTeamPlayer]:
        return await self.team_player.get_players(team)

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        return await self.poll.del_player_vote(team_id, player_id)
