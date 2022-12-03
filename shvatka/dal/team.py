from abc import ABCMeta

from shvatka.dal.base import Reader, Committer
from shvatka.dal.player import TeamJoiner
from shvatka.models import dto


class TeamGetter(Reader):
    async def get_by_chat(self, chat: dto.Chat) -> dto.Team | None:
        raise NotImplementedError


class TeamCreator(TeamJoiner, metaclass=ABCMeta):
    async def check_no_team_in_chat(self, chat: dto.Chat) -> None:
        raise NotImplementedError

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team:
        raise NotImplementedError


class TeamRenamer(Committer, metaclass=ABCMeta):
    async def rename_team(self, team: dto.Team, new_name: str) -> None:
        raise NotImplementedError
