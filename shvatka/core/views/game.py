from __future__ import annotations

import enum
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.models import dto
from shvatka.core.models.dto import action


class GameViewPreparer(Protocol):
    async def prepare_game_view(
        self,
        game: dto.Game,
        teams: Iterable[dto.Team],
        orgs: Iterable[dto.Organizer],
        dao: GamePreparer,
    ) -> None:
        raise NotImplementedError


class InputContainer(Protocol):
    pass


@dataclass(frozen=True)
class ViewTask:
    """One thing to show. Collected before a commit, rendered after it."""


@dataclass(frozen=True)
class KeyShown(ViewTask):
    key: dto.KeyTime
    input_container: InputContainer

    @property
    def team(self) -> dto.Team:
        return self.key.team


@dataclass(frozen=True)
class DuplicateKey(KeyShown):
    pass


@dataclass(frozen=True)
class WrongKey(KeyShown):
    pass


@dataclass(frozen=True)
class EffectsKey(KeyShown):
    effects: action.Effects


@dataclass(frozen=True)
class SendPuzzle(ViewTask):
    team: dto.Team
    level: dto.Level


@dataclass(frozen=True)
class SendHint(ViewTask):
    team: dto.Team
    hint_number: int
    level: dto.Level


@dataclass(frozen=True)
class GameFinished(ViewTask):
    team: dto.Team
    input_container: InputContainer


@dataclass(frozen=True)
class GameFinishedByAll(ViewTask):
    team: dto.Team


@dataclass(frozen=True)
class ShowEffects(ViewTask):
    """Effects without a key: the level timer fired."""

    team: dto.Team
    effects: action.Effects
    input_container: InputContainer


AnyViewTask = (
    DuplicateKey
    | WrongKey
    | EffectsKey
    | SendPuzzle
    | SendHint
    | GameFinished
    | GameFinishedByAll
    | ShowEffects
)
"""A union, not just a base class: a view that forgets a task fails to type."""


def group_by_team(tasks: Sequence[AnyViewTask]) -> list[list[AnyViewTask]]:
    """One list per team, each in order. Different teams may be shown at once."""
    groups: dict[int, list[AnyViewTask]] = {}
    for task in tasks:
        groups.setdefault(task.team.id, []).append(task)
    return list(groups.values())


class GameView(Protocol):
    async def show(self, tasks: Sequence[AnyViewTask]) -> None:
        """Show these. Called after the transaction committed, never before."""
        raise NotImplementedError


class GameLogWriter(Protocol):
    async def log(self, log_event: GameLogEvent) -> None:
        raise NotImplementedError


class GameReleasePublisher(Protocol):
    """Announces a game where the audience is (a telegram channel, ...).

    Whether the release is currently on show, and where — a chat, some message
    ids — is the view's own business, kept by the view and never handed to the
    domain, exactly as pinned messages are.
    """

    async def publish(self, game: dto.Game, release: dto.GameRelease) -> None:
        """Show the release: put it up, or bring what is up to date."""
        raise NotImplementedError

    async def update(self, game: dto.Game, release: dto.GameRelease) -> None:
        """Bring an already shown release up to date. Show nothing new."""
        raise NotImplementedError

    async def unpublish(self, game: dto.Game) -> None:
        """Take the release out of the channel, if it is there."""
        raise NotImplementedError


@dataclass
class ShowTasks:
    """What one request decided to show, one list per sender."""

    view: list[AnyViewTask] = field(default_factory=list)
    org: list[Event] = field(default_factory=list)
    log: list[GameLogEvent] = field(default_factory=list)

    def extend(self, other: ShowTasks) -> None:
        self.view.extend(other.view)
        self.org.extend(other.org)
        self.log.extend(other.log)


class ViewSender(Protocol):
    """Between an interactor and the views: takes what to show, shows nothing."""

    async def show_later(self, tasks: ShowTasks) -> None:
        raise NotImplementedError


class GameLogType(enum.Enum):
    GAME_WAIVERS_STARTED = enum.auto()
    GAME_PLANED = enum.auto()
    GAME_STARTED = enum.auto()
    GAME_FINISHED = enum.auto()
    TEAMS_MERGED = enum.auto()
    PLAYERS_MERGED = enum.auto()
    TEAM_CREATED = enum.auto()


@dataclass
class GameLogEvent:
    type: GameLogType
    data: dict[str, Any] = field(default_factory=dict)


class OrgNotifier(Protocol):
    async def notify(self, event: Event) -> None:
        raise NotImplementedError


@dataclass
class Event:
    orgs_list: Sequence[dto.Organizer]


@dataclass
class LevelUp(Event):
    team: dto.Team
    new_level: dto.Level


@dataclass
class NewOrg(Event):
    game: dto.Game
    org: dto.SecondaryOrganizer


@dataclass
class LevelTestCompleted(Event):
    suite: dto.LevelTestSuite
    result: dto.LevelTestingResult
