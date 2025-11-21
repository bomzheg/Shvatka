from typing import Iterable, Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.player import TeamPlayerGetter, TeamPlayersGetter
from shvatka.core.models import dto
from shvatka.core.waiver.adapters import WaiverVoteGetter


class WaiverApprover(Committer, TeamPlayerGetter, WaiverVoteGetter, TeamPlayersGetter, Protocol):
    async def upsert(self, waiver: dto.Waiver):
        raise NotImplementedError

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError


class GameWaiversGetter(Protocol):
    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def get_played(self, game: dto.Game, team: dto.Team) -> Iterable[dto.VotedPlayer]:
        raise NotImplementedError

    async def get_all_by_game(self, game: dto.Game) -> list[dto.Waiver]:
        raise NotImplementedError


class WaiverMerger(Protocol):
    async def replace_team_waiver(self, primary: dto.Team, secondary: dto.Team):
        raise NotImplementedError


class WaiverChecker(Protocol):
    async def check_waiver(self, player: dto.Player, team: dto.Team, game: dto.Game) -> bool:
        raise NotImplementedError


class WaiverGetter(Protocol):
    async def get_player_waiver(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> dto.Waiver | None:
        raise NotImplementedError
