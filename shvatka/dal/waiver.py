from typing import Iterable

from shvatka.dal.base import Reader, Writer, Committer
from shvatka.models import dto
from shvatka.models.enums.played import Played


class WaiverVoteAdder(Writer):
    async def add_player_vote(self, team_id: int, player_id: int, vote_var: str) -> None: pass

    async def is_excluded(
        self, game: dto.Game, player: dto.Player, team: dto.Team,
    ) -> bool: pass


class PollGetWaivers(Reader):
    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]: pass


class WaiverVoteGetter(PollGetWaivers):
    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]: pass


class WaiverApprover(Committer, WaiverVoteGetter):
    async def upsert(self, waiver: dto.Waiver): pass
