from collections.abc import Iterable
from typing import Protocol

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


class PollVoteRemover(Protocol):
    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        raise NotImplementedError


class AdminPollReader(PollTeamsGetter, WaiverVoteGetter, TeamByIdGetter, Protocol):
    pass


class AdminWaiverEditor(Protocol):
    """Add and remove single waivers on behalf of an admin.

    Everything is addressed by id, and the getters are named apart on purpose:
    a game, a team and a player all answer to ``get_by_id`` in their own dao,
    so composing the narrow protocols here would collide on the name.

    Only the ``waivers`` table is written. The poll draft is a different thing
    with its own button in the panel, and a waiver of a game long over has no
    poll to speak of — so removing one leaves any vote alone.
    """

    async def get_game_by_id(self, id_: int) -> dto.Game:
        raise NotImplementedError

    async def get_team_by_id(self, id_: int) -> dto.Team:
        raise NotImplementedError

    async def get_player_by_id(self, id_: int) -> dto.Player:
        raise NotImplementedError

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        raise NotImplementedError

    async def get_team_waivers(self, game: dto.Game, team: dto.Team) -> list[dto.Waiver]:
        raise NotImplementedError

    async def upsert(self, waiver: dto.Waiver) -> None:
        raise NotImplementedError

    async def delete(self, waiver: dto.WaiverQuery) -> None:
        raise NotImplementedError

    async def commit(self) -> None:
        raise NotImplementedError


class AdminGameWaiversReader(Protocol):
    """Load a game by id and read its approved waivers, for the admin panel."""

    async def get_by_id(self, id_: int) -> dto.Game:
        raise NotImplementedError

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        raise NotImplementedError

    async def get_played(self, game: dto.Game, team: dto.Team) -> Iterable[dto.VotedPlayer]:
        raise NotImplementedError

    async def get_all_by_game(self, game: dto.Game) -> list[dto.Waiver]:
        raise NotImplementedError
