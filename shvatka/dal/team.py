from abc import ABCMeta

from shvatka.dal.base import Reader
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
