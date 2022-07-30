from dataclasses import dataclass
from datetime import datetime

from app.models.enums import GameStatus
from app.models.enums.game_status import active_statuses
from app.utils.datetime_utils import tz_game, tz_utc
from app.utils.exceptions import NotAuthorizedForEdit


@dataclass
class Game:
    id: int
    author_id: int
    name: str
    status: GameStatus
    start_at: datetime
    published_channel_id: int
    manage_token: str

    def is_active(self):
        return self.status in active_statuses

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
        return self.status in (GameStatus.underconstruction, GameStatus.ready, GameStatus.getting_waivers)

    def is_author_id(self, user_id: int) -> bool:
        return self.author_id == user_id

    def check_user_can_edit_game(self, user_id: int):
        if not self.is_author_id(user_id):
            raise NotAuthorizedForEdit(
                "Edit available only for author",
                user_id=user_id, game_id=self.id,
            )
