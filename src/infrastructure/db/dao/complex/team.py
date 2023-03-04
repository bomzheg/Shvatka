from dataclasses import dataclass

from src.infrastructure.db.dao import TeamPlayerDao, TeamDao, GameDao, WaiverDao, PollDao
from src.core.interfaces.dal.player import TeamLeaver
from src.core.interfaces.dal.team import TeamCreator
from src.core.models import dto


@dataclass
class TeamCreatorImpl(TeamCreator):
    team_player: TeamPlayerDao
    team: TeamDao

    async def check_no_team_in_chat(self, chat: dto.Chat) -> None:
        return await self.team.check_no_team_in_chat(chat)

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        return await self.team.create(chat, captain)

    async def join_team(
        self, player: dto.Player, team: dto.Team, role: str, as_captain: bool = False
    ) -> None:
        return await self.team_player.join_team(player, team, role, as_captain)

    async def check_player_free(self, player: dto.Player) -> None:
        return await self.team_player.check_player_free(player)

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.team_player.get_team_player(player)

    async def commit(self) -> None:
        return await self.team.commit()


@dataclass
class TeamLeaverImpl(TeamLeaver):
    game: GameDao
    team_player: TeamPlayerDao
    waiver: WaiverDao
    poll: PollDao

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        return await self.poll.del_player_vote(team_id, player_id)

    async def get_team(self, player: dto.Player) -> dto.Team:
        return await self.team_player.get_team(player)

    async def leave_team(self, player: dto.Player) -> None:
        return await self.team_player.leave_team(player)

    async def get_active_game(self) -> dto.Game | None:
        return await self.game.get_active_game()

    async def delete(self, waiver: dto.Waiver) -> None:
        return await self.waiver.delete(waiver)

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.team_player.get_team_player(player)

    async def commit(self) -> None:
        await self.game.commit()
