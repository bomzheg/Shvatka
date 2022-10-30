from abc import ABCMeta

from shvatka.dal.base import Committer, Reader
from shvatka.dal.game import ActiveGameFinder
from shvatka.models import dto


class PlayerUpserter(Committer, metaclass=ABCMeta):
    async def upsert_player(self, user: dto.User) -> dto.Player:
        raise NotImplementedError


class PlayerTeamChecker(Reader):
    async def have_team(self, player: dto.Player) -> bool:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team:
        raise NotImplementedError

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        raise NotImplementedError


class PlayerInTeamGetter(Reader):
    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        raise NotImplementedError


class PlayerPromoter(Committer, metaclass=ABCMeta):
    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        raise NotImplementedError


class TeamJoiner(Committer, metaclass=ABCMeta):
    async def join_team(self, player: dto.Player, team: dto.Team, role: str) -> None:
        raise NotImplementedError

    async def check_player_free(self, player: dto.Player) -> None:
        raise NotImplementedError


class WaiverRemover(Reader):
    async def delete(self, waiver: dto.Waiver) -> None:
        raise NotImplementedError


class PollVoteDeleter(Reader):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError


class TeamLeaver(Committer, ActiveGameFinder, WaiverRemover, metaclass=ABCMeta):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team:
        raise NotImplementedError

    async def leave_team(self, player: dto.Player) -> None:
        raise NotImplementedError
