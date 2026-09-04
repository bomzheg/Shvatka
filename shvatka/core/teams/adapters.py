from collections.abc import Sequence
from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.complex import TeamMerger
from shvatka.core.interfaces.dal.player import (
    TeamByPlayerGetter,
    TeamJoiner,
    TeamLeaver,
    TeamPlayerEmojiChanger,
    TeamPlayerGetter,
    TeamPlayerPermissionFlipper,
    TeamPlayerRoleChanger,
    TeamPlayersGetter,
)
from shvatka.core.interfaces.dal.team import (
    CaptainedTeamsGetter,
    TeamByIdGetter,
    TeamCaptainChanger,
    TeamDescChanger,
    TeamRenamer,
    TeamsGetter,
)
from shvatka.core.models import dto


class ChatlessTeamCreator(TeamJoiner, Protocol):
    async def create_no_chat(
        self, name: str, description: str | None, captain: dto.Player
    ) -> dto.Team:
        raise NotImplementedError


class TeamPlayerAdder(TeamJoiner, TeamPlayerEmojiChanger, Protocol):
    pass


class TeamPlayerUpdater(
    TeamPlayerRoleChanger,
    TeamPlayerEmojiChanger,
    TeamPlayerPermissionFlipper,
    TeamPlayerGetter,
    Committer,
    Protocol,
):
    pass


class TeamEditor(TeamRenamer, TeamDescChanger, TeamByIdGetter, Protocol):
    pass


class TeamPlayedGamesCounter(Protocol):
    async def get_played_games_counts(self, team_ids: Sequence[int]) -> dict[int, int]:
        raise NotImplementedError


class PlayerPlayedGamesCounter(Protocol):
    async def get_played_games_counts(self, player_ids: Sequence[int]) -> dict[int, int]:
        raise NotImplementedError


class TeamsWithStatGetter(TeamsGetter, TeamPlayedGamesCounter, Protocol):
    pass


class AdminTeamMerger(TeamMerger, TeamByIdGetter, Protocol):
    pass


class TeamCaptainSetter(
    TeamCaptainChanger,
    TeamByIdGetter,
    TeamPlayersGetter,
    TeamPlayerRoleChanger,
    Protocol,
):
    pass


class CaptainedTeamsReader(
    CaptainedTeamsGetter,
    TeamByPlayerGetter,
    TeamPlayedGamesCounter,
    Protocol,
):
    pass


class CaptainTeamJoiner(TeamLeaver, TeamJoiner, TeamByIdGetter, Protocol):
    pass
