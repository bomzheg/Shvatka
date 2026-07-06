from typing import Protocol, Sequence

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.complex import TeamMerger
from shvatka.core.interfaces.dal.player import (
    TeamJoiner,
    TeamPlayerEmojiChanger,
    TeamPlayerGetter,
    TeamPlayerPermissionFlipper,
    TeamPlayerRoleChanger,
)
from shvatka.core.interfaces.dal.team import (
    TeamByIdGetter,
    TeamDescChanger,
    TeamRenamer,
    TeamsGetter,
)
from shvatka.core.models import dto


class ChatlessTeamCreator(TeamJoiner, Protocol):
    """DAO contract for creating a team that is not bound to any telegram chat."""

    async def create_no_chat(
        self, name: str, description: str | None, captain: dto.Player
    ) -> dto.Team:
        raise NotImplementedError


class TeamPlayerAdder(TeamJoiner, TeamPlayerEmojiChanger, Protocol):
    """DAO contract for adding a player into a team (with optional emoji)."""


class TeamPlayerUpdater(
    TeamPlayerRoleChanger,
    TeamPlayerEmojiChanger,
    TeamPlayerPermissionFlipper,
    TeamPlayerGetter,
    Committer,
    Protocol,
):
    """DAO contract for editing an existing team player."""


class TeamEditor(TeamRenamer, TeamDescChanger, TeamByIdGetter, Protocol):
    """DAO contract for renaming a team and changing its description."""


class TeamPlayedGamesCounter(Protocol):
    """DAO contract for counting played games per team in one query."""

    async def get_played_games_counts(self, team_ids: Sequence[int]) -> dict[int, int]:
        raise NotImplementedError


class PlayerPlayedGamesCounter(Protocol):
    """DAO contract for counting played games per player in one query."""

    async def get_played_games_counts(self, player_ids: Sequence[int]) -> dict[int, int]:
        raise NotImplementedError


class TeamsWithStatGetter(TeamsGetter, TeamPlayedGamesCounter, Protocol):
    """DAO contract for listing teams together with their played games counts."""


class AdminTeamMerger(TeamMerger, TeamByIdGetter, Protocol):
    """Merge one team into another, plus load both by id."""
