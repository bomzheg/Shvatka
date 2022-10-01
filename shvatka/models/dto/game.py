from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from db import models
from shvatka.config.constants import TIME_TO_PREPARING_GAME
from shvatka.models.enums import GameStatus
from shvatka.models.enums.game_status import ACTIVE_STATUSES, EDITABLE_STATUSES
from shvatka.utils.datetime_utils import tz_game, tz_utc
from .level import Level
from .player import Player


@dataclass
class Game:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime
    published_channel_id: int
    manage_token: str
    levels: list[Level] = field(default_factory=list)

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
    def can_set_start_datetime(self) -> bool:
        return self.status in (GameStatus.ready, GameStatus.getting_waivers)

    @property
    def can_be_publish(self) -> bool:
        return self.status in (GameStatus.finished,)

    @property
    def can_change_name(self) -> bool:
        return self.status in (GameStatus.underconstruction, GameStatus.ready)

    @property
    def can_be_edited(self) -> bool:
        return self.status in EDITABLE_STATUSES

    def is_author_id(self, player_id: int) -> bool:
        return self.author.id == player_id

    @classmethod
    def from_db(cls, game: models.Game, author: Player) -> Game:
        return cls(
            id=game.id,
            author=author,
            name=game.name,
            status=game.status,
            start_at=game.start_at,
            published_channel_id=game.published_channel_id,
            manage_token=game.manage_token,
        )
