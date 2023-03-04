from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.shvatka.config.constants import TIME_TO_PREPARING_GAME
from src.shvatka.models.enums import GameStatus
from src.shvatka.models.enums.game_status import ACTIVE_STATUSES, EDITABLE_STATUSES
from src.shvatka.utils.datetime_utils import tz_game, tz_utc
from .level import Level
from .player import Player
from .scn.time_hint import TimeHint


@dataclass
class Game:
    id: int
    author: Player
    name: str
    status: GameStatus
    manage_token: str
    start_at: datetime | None
    number: int | None
    published_channel_id: int | None

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
        ) and self.published_channel_id is None

    @property
    def can_change_name(self) -> bool:
        return self.status in (GameStatus.underconstruction, GameStatus.ready)

    @property
    def can_be_edited(self) -> bool:
        return self.status in EDITABLE_STATUSES

    def is_author_id(self, player_id: int) -> bool:
        return self.author.id == player_id

    def to_full_game(self, levels: list[Level]) -> FullGame:
        return FullGame(
            id=self.id,
            author=self.author,
            name=self.name,
            status=self.status,
            start_at=self.start_at,
            published_channel_id=self.published_channel_id,
            manage_token=self.manage_token,
            levels=levels,
            number=self.number,
        )


@dataclass
class FullGame(Game):
    levels: list[Level] = field(default_factory=list)

    def get_guids(self) -> list[str]:
        guids = []
        for hint in self.levels:
            guids.extend(hint.get_guids())
        return guids

    def get_hint(self, level_number: int, hint_number: int) -> TimeHint:
        return self.levels[level_number].get_hint(hint_number)

    @property
    def hints_count(self) -> int:
        return sum((level.hints_count for level in self.levels))
