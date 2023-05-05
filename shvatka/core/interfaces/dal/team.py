from typing import Protocol, Sequence

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.player import TeamJoiner
from shvatka.core.models import dto


class TeamGetter(Protocol):
    async def get_by_chat(self, chat: dto.Chat) -> dto.Team | None:
        raise NotImplementedError


class TeamCreator(TeamJoiner, Protocol):
    async def check_no_team_in_chat(self, chat: dto.Chat) -> None:
        raise NotImplementedError

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        raise NotImplementedError


class TeamRenamer(Committer, Protocol):
    async def rename_team(self, team: dto.Team, new_name: str) -> None:
        raise NotImplementedError


class TeamDescChanger(Committer, Protocol):
    async def change_team_desc(self, team: dto.Team, new_desc: str) -> None:
        raise NotImplementedError


class TeamsGetter(Protocol):
    async def get_teams(self, active: bool = True, archive: bool = False) -> list[dto.Team]:
        raise NotImplementedError


class TeamByIdGetter(Protocol):
    async def get_by_id(self, id_: int) -> dto.Team:
        raise NotImplementedError


class PlayedGamesByTeamGetter(Protocol):
    async def get_played_games(self, team: dto.Team) -> list[dto.Game]:
        raise NotImplementedError


class ForumTeamMerger(Protocol):
    async def replace_forum_team(self, primary: dto.Team, secondary: dto.Team):
        raise NotImplementedError


class FreeForumTeamGetter(Protocol):
    async def get_free_forum_teams(self) -> Sequence[dto.ForumTeam]:
        raise NotImplementedError


class ByForumTeamIdGetter(Protocol):
    async def get_by_forum_team_id(self, forum_team_id: int) -> dto.Team:
        raise NotImplementedError


class TeamRemover(Protocol):
    async def delete(self, team: dto.Team):
        raise NotImplementedError
