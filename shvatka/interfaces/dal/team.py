from typing import Protocol

from shvatka.interfaces.dal.base import Committer
from shvatka.interfaces.dal.player import TeamJoiner
from shvatka.models import dto


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
