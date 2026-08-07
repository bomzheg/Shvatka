from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from shvatka.core.config.constants import TIME_TO_PREPARING_GAME
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.game_status import ACTIVE_STATUSES, EDITABLE_STATUSES
from shvatka.core.utils.datetime_utils import tz_game, tz_utc
from . import hints
from .hints import AnyHint
from .level import GamedLevel
from .player import Player


@dataclass
class Game:
    id: int
    author: Player
    name: str
    status: GameStatus
    manage_token: str
    start_at: datetime | None
    number: int | None
    results: GameResults

    def is_active(self):
        return self.status in ACTIVE_STATUSES

    def is_getting_waivers(self):
        return self.status == GameStatus.getting_waivers

    def is_started(self):
        return self.status == GameStatus.started

    def is_finished(self):
        return self.status == GameStatus.finished

    def is_complete(self):
        return self.status == GameStatus.complete

    def get_started_datetime(self, tz=tz_game):
        return self.start_at.astimezone(tz=tz)

    def get_utc_start_datetime(self):
        return self.get_started_datetime(tz=tz_utc)

    @property
    def prepared_at(self):
        return self.start_at - timedelta(minutes=TIME_TO_PREPARING_GAME)

    @property
    def can_be_delete(self) -> bool:
        return self.status in (GameStatus.underconstruction, GameStatus.ready)

    @property
    def can_start_waivers(self) -> bool:
        return self.status in (GameStatus.underconstruction, GameStatus.ready)

    @property
    def can_set_start_datetime(self) -> bool:
        return self.status in (GameStatus.ready, GameStatus.getting_waivers)

    @property
    def can_be_publish(self) -> bool:
        return (
            self.status in (GameStatus.finished, GameStatus.complete)
        ) and self.results.published_chanel_id is None

    @property
    def can_change_name(self) -> bool:
        return self.status in (GameStatus.underconstruction, GameStatus.ready)

    @property
    def can_be_edited(self) -> bool:
        return self.status in EDITABLE_STATUSES

    def is_author_id(self, player_id: int) -> bool:
        return self.author.id == player_id

    def to_full_game(self, levels: list[GamedLevel]) -> FullGame:
        return FullGame(
            id=self.id,
            author=self.author,
            name=self.name,
            status=self.status,
            start_at=self.start_at,
            results=self.results,
            manage_token=self.manage_token,
            levels=levels,
            number=self.number,
        )


@dataclass
class PreviewGame(Game):
    levels_count: int

    @classmethod
    def from_game(cls, self: Game, levels_count: int) -> PreviewGame:
        return cls(
            id=self.id,
            author=self.author,
            name=self.name,
            status=self.status,
            start_at=self.start_at,
            results=self.results,
            manage_token=self.manage_token,
            number=self.number,
            levels_count=levels_count,
        )


@dataclass
class FullGame(Game):
    levels: list[GamedLevel] = field(default_factory=list)

    def get_guids(self) -> list[str]:
        guids = []
        for level in self.levels:
            guids.extend(level.get_guids())
        return guids

    def get_hint(self, level_number: int, hint_number: int) -> hints.TimeHint:
        return self.levels[level_number].get_hint(hint_number)

    @property
    def hints_count(self) -> int:
        return sum(level.hints_count for level in self.levels)


@dataclass
class ReleasePost:
    """Where a release currently lives in the announcements channel.

    One message per hint, in order, so editing the release edits exactly these
    messages instead of posting the whole thing again.
    """

    chat_id: int
    message_ids: list[int]


@dataclass
class GameRelease:
    """A game's release — the promo published before it.

    It leads with a *banner*: a wide title picture with a caption, the one part
    of a release small enough to stand above the site's header. Everything
    after it — the theme, the map, the rules — is a plain list of hints, so the
    whole existing hint machinery (editors, senders, renderers) works for it as
    is.

    Both halves are optional, and so is the release itself: a game without one
    is played exactly as before.

    Saving a release and announcing it are separate: it can be written and
    rewritten any time, and it goes to the channel when the game starts
    collecting waivers.
    """

    game_id: int
    banner: hints.PhotoHint | None = None
    hints: list[hints.AnyHint] = field(default_factory=list)
    post: ReleasePost | None = None

    @property
    def is_published(self) -> bool:
        return self.post is not None

    @property
    def is_empty(self) -> bool:
        return self.banner is None and not self.hints

    @property
    def parts(self) -> list[AnyHint]:
        """The whole release in the order it is shown — the banner leads."""
        if self.banner is None:
            return list(self.hints)
        return [self.banner, *self.hints]

    def get_guids(self) -> list[str]:
        guids = []
        for hint in self.parts:
            guids.extend(hint.get_guids())
        return guids


@dataclass
class GameResults:
    published_chanel_id: int | None
    results_picture_file_id: str | None
    keys_url: str | None


@dataclass
class GameFinished:
    game: Game
