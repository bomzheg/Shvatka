from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models import dto


@dataclass(frozen=True)
class KeyTime:
    text: str
    is_correct: bool
    is_duplicate: bool
    at: datetime
    level_number: int
    player: dto.Player
    team: dto.Team


@dataclass(frozen=True)
class InsertedKey(KeyTime):
    is_level_up: bool

    @classmethod
    def from_key_time(cls, key_time: KeyTime, is_level_up: bool):
        return cls(
            text=key_time.text,
            is_correct=key_time.is_correct,
            is_duplicate=key_time.is_duplicate,
            at=key_time.at,
            level_number=key_time.level_number,
            player=key_time.player,
            is_level_up=is_level_up,
            team=key_time.team,
        )


@dataclass
class KeyInsertResult:
    is_correct: bool
    is_duplicate: bool
    level_completed: bool
    game_finished: bool

    @classmethod
    def wrong(cls):
        return cls(
            is_correct=False,
            is_duplicate=False,
            level_completed=False,
            game_finished=False,
        )

    @classmethod
    def correct(cls):
        return cls(
            is_correct=True,
            is_duplicate=False,
            level_completed=False,
            game_finished=False,
        )

    @classmethod
    def completed(cls):
        return cls(
            is_correct=True,
            is_duplicate=False,
            level_completed=True,
            game_finished=False,
        )
