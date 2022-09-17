from typing import Protocol

from shvatka.dal.base import Committer
from shvatka.models import dto


class PlayerUpserter(Protocol, Committer):
    async def upsert_player(self, user: dto.User) -> dto.Player: pass


class PlayerTeamChecker(Protocol):
    async def have_team(self, player: dto.Player) -> bool: pass

    async def get_team(self, player: dto.Player) -> dto.Team: pass

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam: pass


class PlayerPromoter(Protocol, Committer):
    async def promote(self, actor: dto.Player, target: dto.Player) -> None: pass


class TeamJoiner(Protocol, Committer):
    async def join_team(self, player: dto.Player, team: dto.Team, role: str) -> None: pass


class ActiveGameFinder(Protocol):
    async def get_active_game(self) -> dto.Game | None: pass


class PlayerTeamLeaver(Protocol):
    async def leave_team(self, player: dto.Player) -> None: pass


class WaiverRemover(Protocol):
    async def delete(self, waiver: dto.Waiver) -> None: pass


class PollVoteDeleter(Protocol):
    async def del_player_vote(self, team_id: int, player_id: int) -> None: pass


class TeamLeaver(Protocol, Committer):
    class _PlayerTeamCheckerAndLeaver(PlayerTeamChecker, PlayerTeamLeaver):
        pass

    game: ActiveGameFinder
    team: PlayerTeamChecker
    player_in_team: _PlayerTeamCheckerAndLeaver
    waiver: WaiverRemover
    poll: PollVoteDeleter
