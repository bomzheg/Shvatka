from abc import ABCMeta

from shvatka.interfaces.dal.base import Committer, Reader
from shvatka.interfaces.dal.game import ActiveGameFinder
from shvatka.interfaces.dal.secure_invite import InviteRemover, InviteReader
from shvatka.models import dto, enums


class PlayerUpserter(Committer, metaclass=ABCMeta):
    async def upsert_player(self, user: dto.User) -> dto.Player:
        raise NotImplementedError


class PlayerByIdGetter(Reader):
    async def get_by_id(self, id_: int) -> dto.Player:
        raise NotImplementedError


class TeamPlayerGetter(Reader):
    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        raise NotImplementedError


class PlayerTeamChecker(TeamPlayerGetter, metaclass=ABCMeta):
    async def have_team(self, player: dto.Player) -> bool:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team:
        raise NotImplementedError


class PlayerPromoter(Committer, PlayerByIdGetter, InviteReader, InviteRemover, metaclass=ABCMeta):
    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        raise NotImplementedError


class TeamJoiner(Committer, TeamPlayerGetter, metaclass=ABCMeta):
    async def join_team(self, player: dto.Player, team: dto.Team, role: str, as_captain: bool = False) -> None:
        raise NotImplementedError

    async def check_player_free(self, player: dto.Player) -> None:
        raise NotImplementedError


class WaiverRemover(Reader):
    async def delete(self, waiver: dto.Waiver) -> None:
        raise NotImplementedError


class PollVoteDeleter(Reader):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError


class TeamLeaver(Committer, ActiveGameFinder, WaiverRemover, TeamPlayerGetter, metaclass=ABCMeta):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team:
        raise NotImplementedError

    async def leave_team(self, player: dto.Player) -> None:
        raise NotImplementedError


class TeamPlayersGetter(Reader):
    async def get_players(self, team: dto.Team) -> list[dto.FullTeamPlayer]:
        raise NotImplementedError


class TeamPlayerPermissionFlipper(Committer):
    async def flip_permission(self, player: dto.TeamPlayer, permission: enums.TeamPlayerPermission):
        raise NotImplementedError