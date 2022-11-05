from abc import ABCMeta
from typing import Iterable

from shvatka.dal.base import Reader, Writer, Committer
from shvatka.dal.player import PlayerInTeamGetter
from shvatka.models import dto
from shvatka.models.enums.played import Played


class WaiverVoteAdder(Writer, PlayerInTeamGetter):
    async def add_player_vote(self, team_id: int, player_id: int, vote_var: str) -> None:
        raise NotImplementedError

    async def is_excluded(
        self, game: dto.Game, player: dto.Player, team: dto.Team,
    ) -> bool:
        raise NotImplementedError

    async def get_player_in_team(self, player: dto.Player) -> dto.PlayerInTeam:
        raise NotImplementedError


class PollGetWaivers(Reader):
    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        raise NotImplementedError


class WaiverVoteGetter(PollGetWaivers, metaclass=ABCMeta):
    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        raise NotImplementedError


class WaiverApprover(Committer, WaiverVoteGetter, PlayerInTeamGetter, metaclass=ABCMeta):
    async def upsert(self, waiver: dto.Waiver):
        raise NotImplementedError
