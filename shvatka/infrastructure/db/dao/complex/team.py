import typing
from dataclasses import dataclass

from shvatka.core.interfaces.dal.complex import TeamMerger
from shvatka.core.interfaces.dal.player import TeamLeaver
from shvatka.core.interfaces.dal.team import TeamCreator
from shvatka.core.models import dto

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class TeamCreatorImpl(TeamCreator):
    dao: "HolderDao"

    async def check_no_team_in_chat(self, chat: dto.Chat) -> None:
        return await self.dao.team.check_no_team_in_chat(chat)

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        return await self.dao.team.create(chat, captain)

    async def join_team(
        self, player: dto.Player, team: dto.Team, role: str, as_captain: bool = False
    ) -> None:
        return await self.dao.team_player.join_team(player, team, role, as_captain)

    async def check_player_free(self, player: dto.Player) -> None:
        return await self.dao.team_player.check_player_free(player)

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.dao.team_player.get_team_player(player)

    async def commit(self) -> None:
        return await self.dao.commit()


@dataclass
class TeamLeaverImpl(TeamLeaver):
    dao: "HolderDao"

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        return await self.dao.poll.del_player_vote(team_id, player_id)

    async def get_team(self, player: dto.Player) -> dto.Team:
        return await self.dao.team_player.get_team(player)

    async def leave_team(self, player: dto.Player) -> None:
        return await self.dao.team_player.leave_team(player)

    async def get_active_game(self) -> dto.Game | None:
        return await self.dao.game.get_active_game()

    async def delete(self, waiver: dto.Waiver) -> None:
        return await self.dao.waiver.delete(waiver)

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.dao.team_player.get_team_player(player)

    async def commit(self) -> None:
        await self.dao.commit()


@dataclass
class TeamMergerImpl(TeamMerger):
    dao: "HolderDao"

    async def replace_team_waiver(self, primary: dto.Team, secondary: dto.Team):
        return await self.dao.waiver.replace_team_waiver(primary, secondary)

    async def replace_team_keys(self, primary: dto.Team, secondary: dto.Team):
        return await self.dao.key_time.replace_team_keys(primary, secondary)

    async def replace_team_levels(self, primary: dto.Team, secondary: dto.Team):
        return await self.dao.level_time.replace_team_levels(primary, secondary)

    async def replace_team_players(self, primary: dto.Team, secondary: dto.Team):
        return await self.dao.team_player.replace_team_players(primary, secondary)

    async def replace_forum_team(self, primary: dto.Team, secondary: dto.Team):
        return await self.dao.forum_team.replace_forum_team(primary, secondary)

    async def delete(self, team: dto.Team):
        return await self.dao.team.delete(team)

    async def commit(self) -> None:
        return await self.dao.commit()
