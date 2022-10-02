from shvatka.dal.base import Reader
from shvatka.dal.player import TeamJoiner
from shvatka.models import dto


class TeamGetter(Reader):
    async def get_by_chat(self, chat: dto.Chat) -> dto.Team | None:
        pass


class TeamCreator(TeamJoiner):
    async def check_no_team_in_chat(self, chat: dto.Chat) -> None: pass

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team: pass

