from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
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
)


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
