from dataclasses import dataclass
from typing import Iterable

from db.dao import PollDao, WaiverDao, PlayerDao, PlayerInTeamDao
from shvatka.dal.waiver import WaiverVoteAdder, WaiverVoteGetter, WaiverApprover
from shvatka.models import dto
from shvatka.models.enums.played import Played


@dataclass
class WaiverVoteAdderImpl(WaiverVoteAdder):
    poll: PollDao
    waiver: WaiverDao
    player_in_team: PlayerInTeamDao

    async def is_excluded(
        self, game: dto.Game, player: dto.Player, team: dto.Team,
    ) -> bool:
        return await self.waiver.is_excluded(game, player, team)

    async def add_player_vote(self, team_id: int, player_id: int, vote_var: str) -> None:
        return await self.poll.add_player_vote(team_id, player_id, vote_var)

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        return await self.player_in_team.get_player_in_team(player)


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
    player_in_team: PlayerInTeamDao

    async def upsert(self, waiver: dto.Waiver) -> None:
        return await self.waiver.upsert(waiver)

    async def commit(self):
        return await self.waiver.commit()

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        return await self.player_in_team.get_player_in_team(player)

    async def get_players(self, team: dto.Team) -> list[dto.FullTeamPlayer]:
        return await self.player_in_team.get_players(team)

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        return await self.poll.del_player_vote(team_id, player_id)
