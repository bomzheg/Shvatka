from typing import Protocol

from shvatka.interfaces.dal.base import Committer
from shvatka.interfaces.dal.game import ActiveGameFinder
from shvatka.interfaces.dal.secure_invite import InviteRemover, InviteReader
from shvatka.models import dto, enums


class PlayerUpserter(Protocol, Committer):
    async def upsert_player(self, user: dto.User) -> dto.Player:
        raise NotImplementedError


class PlayerByIdGetter(Protocol):
    async def get_by_id(self, id_: int) -> dto.Player:
        raise NotImplementedError


class TeamPlayerGetter(Protocol):
    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        raise NotImplementedError


class PlayerTeamChecker(Protocol, TeamPlayerGetter):
    async def have_team(self, player: dto.Player) -> bool:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team | None:
        raise NotImplementedError


class PlayerPromoter(Protocol, Committer, PlayerByIdGetter, InviteReader, InviteRemover):
    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        raise NotImplementedError


class TeamJoiner(Protocol, Committer, TeamPlayerGetter):
    async def join_team(
        self, player: dto.Player, team: dto.Team, role: str, as_captain: bool = False
    ) -> None:
        raise NotImplementedError

    async def check_player_free(self, player: dto.Player) -> None:
        raise NotImplementedError


class WaiverRemover(Protocol):
    async def delete(self, waiver: dto.Waiver) -> None:
        raise NotImplementedError


class PollVoteDeleter(Protocol):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError


class TeamLeaver(Protocol, Committer, ActiveGameFinder, WaiverRemover, TeamPlayerGetter):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError

    async def get_team(self, player: dto.Player) -> dto.Team:
        raise NotImplementedError

    async def leave_team(self, player: dto.Player) -> None:
        raise NotImplementedError


class TeamPlayersGetter(Protocol):
    async def get_players(self, team: dto.Team) -> list[dto.FullTeamPlayer]:
        raise NotImplementedError


class TeamPlayerPermissionFlipper(Protocol, Committer):
    async def flip_permission(
        self, player: dto.TeamPlayer, permission: enums.TeamPlayerPermission
    ):
        raise NotImplementedError
