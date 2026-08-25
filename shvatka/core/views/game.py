from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Protocol, Iterable, Sequence, Any

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
    """One thing the game has to show, as data rather than as a call.

    An interactor decides *what* to show while it still holds the transaction,
    and collects the tasks in a plain list. Nothing is shown until it commits
    and hands the list to :meth:`GameView.show` — so a transaction that never
    lands shows nothing, which is the whole point of the shape.

    A task must be self-contained: it carries the dtos a view needs and
    survives the scope it was made in, because it is usually rendered later,
    somewhere else.
    """


@dataclass(frozen=True)
class KeyShown(ViewTask):
    """The team typed a key and has to be told what it was.

    Grouped under one base because the answer to a key is also what the http
    response is built from — the api picks this out of the list without caring
    which of the three it is.
    """

    key: dto.KeyTime
    input_container: InputContainer


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
    """Effects that happened without a key — the level timer fired."""

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
"""Every task there is, as a union — so a view that forgets one fails to type."""


class GameView(Protocol):
    """Shows the game wherever its audience is — a chat, a browser, both.

    One method on purpose: a view decides for itself how to render each task,
    and how to render a whole batch — the telegram one hands the batch to a
    background task so a player never waits for it. Adding something to show
    is a new :class:`ViewTask`, not a new method every implementation has to
    grow.
    """

    async def show(self, tasks: Sequence[AnyViewTask]) -> None:
        """Show these, in this order. Called after the transaction committed."""
        raise NotImplementedError


class GameLogWriter(Protocol):
    async def log(self, log_events: Sequence[GameLogEvent]) -> None:
        """Write these down where the audience of the game watches it."""
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
    """What one request decided to show, one plain list per sender.

    Filled while the interactor still holds the transaction and handed over
    only after it commits, so a transaction that never lands shows nothing.
    Separate lists because the three senders are separate: order is kept
    within a list, never between them.
    """

    view: list[AnyViewTask] = field(default_factory=list)
    org: list[Event] = field(default_factory=list)
    log: list[GameLogEvent] = field(default_factory=list)

    def extend(self, other: ShowTasks) -> None:
        self.view.extend(other.view)
        self.org.extend(other.org)
        self.log.extend(other.log)


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
    async def notify(self, events: Sequence[Event]) -> None:
        """Tell the orgs about these, in this order."""
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
