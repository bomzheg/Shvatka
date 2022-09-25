from shvatka.dal.base import Reader, Committer, Writer
from shvatka.dal.player import TeamJoiner
from shvatka.models import dto


class TeamGetter(Reader):
    async def get_by_chat(self, chat: dto.Chat) -> dto.Team | None:
        pass


class TeamJustCreator(Writer):
    async def check_no_team_in_chat(self, chat: dto.Chat): pass

    async def create(self, chat: dto.Chat, captain: dto.Player) -> dto.Team: pass


class TeamCreator(Committer):
    player_in_team: TeamJoiner
    team: TeamJustCreator

