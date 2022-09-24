from shvatka.dal.base import Committer, Reader
from shvatka.models import dto


class PlayerUpserter(Committer):
    async def upsert_player(self, user: dto.User) -> dto.Player: pass


class PlayerTeamChecker(Reader):
    async def have_team(self, player: dto.Player) -> bool: pass

    async def get_team(self, player: dto.Player) -> dto.Team: pass

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam: pass


class PlayerPromoter(Committer):
    async def promote(self, actor: dto.Player, target: dto.Player) -> None: pass


class TeamJoiner(Committer):
    async def join_team(self, player: dto.Player, team: dto.Team, role: str) -> None: pass


class ActiveGameFinder(Reader):
    async def get_active_game(self) -> dto.Game | None: pass


class PlayerTeamLeaver(Reader):
    async def leave_team(self, player: dto.Player) -> None: pass


class WaiverRemover(Reader):
    async def delete(self, waiver: dto.Waiver) -> None: pass


class PollVoteDeleter(Reader):
    async def del_player_vote(self, team_id: int, player_id: int) -> None: pass


class TeamLeaver(Committer):
    class _PlayerTeamCheckerAndLeaver(PlayerTeamChecker, PlayerTeamLeaver):
        pass

    game: ActiveGameFinder
    team: PlayerTeamChecker
    player_in_team: _PlayerTeamCheckerAndLeaver
    waiver: WaiverRemover
    poll: PollVoteDeleter
