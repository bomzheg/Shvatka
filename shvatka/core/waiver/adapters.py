from typing import Protocol, Iterable

from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.core.interfaces.dal.player import TeamPlayerGetter
from shvatka.core.interfaces.dal.team import TeamByIdGetter
from shvatka.core.models import dto
from shvatka.core.models.enums import Played


class WaiverVoteAdder(TeamPlayerGetter, Protocol):
    async def add_player_vote(self, team_id: int, player_id: int, vote_var: str) -> None:
        raise NotImplementedError

    async def is_excluded(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> bool:
        raise NotImplementedError

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        raise NotImplementedError


class PollGetWaivers(Protocol):
    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        raise NotImplementedError


class PollTeamsGetter(Protocol):
    async def get_polled_teams(self) -> list[int]:
        raise NotImplementedError


class WaiverVoteGetter(PollGetWaivers, Protocol):
    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        raise NotImplementedError


class PollDraftsReader(
    PollTeamsGetter, WaiverVoteGetter, TeamByIdGetter, OrgByPlayerGetter, Protocol
):
    pass
