from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models import dto, enums
from . import action


@dataclass(frozen=True)
class KeyTime:
    text: action.SHKey
    type_: enums.KeyType
    is_duplicate: bool
    at: datetime
    level_number: int
    player: dto.Player
    team: dto.Team


@dataclass(frozen=True)
class InsertedKey(KeyTime):
    level_up: bool
    parsed_key: ParsedKey

    def is_level_up(self) -> bool:
        return self.level_up or self.parsed_key.effect.level_up

    @classmethod
    def from_key_time(cls, key_time: KeyTime, is_level_up: bool, parsed_key: ParsedKey):
        return cls(
            text=key_time.text,
            type_=key_time.type_,
            is_duplicate=key_time.is_duplicate,
            at=key_time.at,
            level_number=key_time.level_number,
            player=key_time.player,
            level_up=is_level_up,
            team=key_time.team,
            parsed_key=parsed_key,
        )


@dataclass
class KeyInsertResult:
    type_: enums.KeyType
    is_duplicate: bool
    level_completed: bool
    game_finished: bool

    @classmethod
    def wrong(cls):
        return cls(
            type_=enums.KeyType.wrong,
            is_duplicate=False,
            level_completed=False,
            game_finished=False,
        )

    @classmethod
    def correct(cls):
        return cls(
            type_=enums.KeyType.simple,
            is_duplicate=False,
            level_completed=False,
            game_finished=False,
        )

    @classmethod
    def completed(cls):
        return cls(
            type_=enums.KeyType.simple,
            is_duplicate=False,
            level_completed=True,
            game_finished=False,
        )


@dataclass(kw_only=True)
class ParsedKey:
    text: str
    type_: enums.KeyType
    effect: action.Effects
