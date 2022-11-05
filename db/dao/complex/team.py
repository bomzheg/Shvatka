from dataclasses import dataclass

from db.dao import PlayerInTeamDao, TeamDao, GameDao, WaiverDao, PollDao
from shvatka.dal.player import TeamLeaver
from shvatka.dal.team import TeamCreator
from shvatka.models import dto


@dataclass
class TeamCreatorImpl(TeamCreator):
    player_in_team: PlayerInTeamDao
    team: TeamDao

    async def check_no_team_in_chat(self, chat: dto.Chat):
        return await self.team.check_no_team_in_chat(chat)

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        return await self.team.create(chat, captain)

    async def join_team(self, player: dto.Player, team: dto.Team, role: str) -> None:
        return await self.player_in_team.join_team(player, team, role)

    async def check_player_free(self, player: dto.Player) -> None:
        return await self.player_in_team.check_player_free(player)

    async def commit(self):
        return await self.team.commit()


@dataclass
class TeamLeaverImpl(TeamLeaver):
    game: GameDao
    player_in_team: PlayerInTeamDao
    waiver: WaiverDao
    poll: PollDao

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        return await self.poll.del_player_vote(team_id, player_id)

    async def get_team(self, player: dto.Player) -> dto.Team:
        return await self.player_in_team.get_team(player)

    async def leave_team(self, player: dto.Player) -> None:
        return await self.player_in_team.leave_team(player)

    async def get_active_game(self) -> dto.Game | None:
        return await self.game.get_active_game()

    async def delete(self, waiver: dto.Waiver) -> None:
        return await self.waiver.delete(waiver)

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        return await self.player_in_team.get_player_in_team(player)

    async def commit(self) -> None:
        await self.game.commit()
