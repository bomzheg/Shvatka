import dataclasses
import enum
from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models import enums, dto


class PlayerIdentity(enum.StrEnum):
    forum_name = enum.auto()
    tg_user_id = enum.auto()


class TeamIdentity(enum.StrEnum):
    forum_name = enum.auto()
    bomzheg_engine_name = enum.auto()


@dataclass
class LevelTime:
    number: int
    at: datetime | None

    @classmethod
    def from_dto(cls, lt: dto.LevelTime):
        return cls(
            number=lt.level_number,
            at=lt.start_at,
        )


@dataclass
class Key:
    level: int
    player: str | int
    at: datetime
    value: str
    player_identity: PlayerIdentity = PlayerIdentity.forum_name

    @classmethod
    def from_dto(cls, key_time: dto.KeyTime):
        player_tg_id = key_time.player.get_chat_id()
        assert player_tg_id is not None
        return cls(
            level=key_time.level_number,
            player=player_tg_id,
            at=key_time.at,
            value=key_time.text,
            player_identity=PlayerIdentity.tg_user_id,
        )


@dataclass
class Waiver:
    player: str | int
    player_identity: PlayerIdentity
    team: str
    team_identity: TeamIdentity
    vote: enums.Played = enums.Played.yes


@dataclass
class GameStat:
    id: int
    start_at: datetime
    results: dict[str, list[LevelTime]]
    keys: dict[str, list[Key]]
    waivers: list[Waiver] = dataclasses.field(default_factory=list)
    team_identity: TeamIdentity = TeamIdentity.forum_name
