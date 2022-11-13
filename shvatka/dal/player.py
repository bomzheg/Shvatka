from abc import ABCMeta

from shvatka.dal.base import Committer, Reader
from shvatka.dal.game import ActiveGameFinder
from shvatka.dal.secure_invite import InviteRemover, InviteReader
from shvatka.models import dto


class PlayerUpserter(Committer, metaclass=ABCMeta):
    async def upsert_player(self, user: dto.User) -> dto.Player:
        raise NotImplementedError


class PlayerByIdGetter(Reader):
    async def get_by_id(self, id_: int) -> dto.Player:
        raise NotImplementedError


class PlayerInTeamGetter(Reader):
    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        raise NotImplementedError


class PlayerTeamChecker(PlayerInTeamGetter, metaclass=ABCMeta):
    async def have_team(self, player: dto.Player) -> bool:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team:
        raise NotImplementedError


class PlayerPromoter(Committer, PlayerByIdGetter, InviteReader, InviteRemover, metaclass=ABCMeta):
    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        raise NotImplementedError


class TeamJoiner(Committer, PlayerInTeamGetter, metaclass=ABCMeta):
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


class TeamLeaver(Committer, ActiveGameFinder, WaiverRemover, PlayerInTeamGetter, metaclass=ABCMeta):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team:
        raise NotImplementedError

    async def leave_team(self, player: dto.Player) -> None:
        raise NotImplementedError
