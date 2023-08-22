import dataclasses
import enum
import typing
from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models import enums

if typing.TYPE_CHECKING:
    from shvatka.core.models import dto


class PlayerIdentity(enum.StrEnum):
    forum_name = enum.auto()
    tg_user_id = enum.auto()


class TeamIdentity(enum.StrEnum):
    forum_name = enum.auto()
    bomzheg_engine_name = enum.auto()


@dataclass
class Player:
    identity: PlayerIdentity
    forum_name: str | None = None
    tg_user_id: int | None = None

    def __post_init__(self) -> None:
        if self.forum_name is None and self.tg_user_id is None:
            raise RuntimeError("forum name and tg_user_id are None both")

    @classmethod
    def from_dto(cls, player: "dto.Player"):
        if player.has_user():
            player_tg_id = player.get_chat_id()
            assert player_tg_id is not None
            player_identity = PlayerIdentity.tg_user_id
            return Player(tg_user_id=player_tg_id, identity=player_identity)
        elif player.has_forum_user():
            player_name = player.get_forum_name()
            assert player_name is not None
            player_identity = PlayerIdentity.forum_name
            return Player(forum_name=player_name, identity=player_identity)
        else:
            raise RuntimeError("player without user and forum_user")


@dataclass
class LevelTime:
    number: int
    at: datetime | None

    @classmethod
    def from_dto(cls, lt: "dto.LevelTime"):
        return cls(
            number=lt.level_number,
            at=lt.start_at,
        )


@dataclass
class Key:
    level: int
    player: Player
    at: datetime
    value: str

    @classmethod
    def from_dto(cls, key_time: "dto.KeyTime"):
        return cls(
            level=key_time.level_number,
            at=key_time.at,
            value=key_time.text,
            player=Player.from_dto(key_time.player),
        )


@dataclass
class Waiver:
    player: Player
    team: str
    team_identity: TeamIdentity
    played: enums.Played = enums.Played.yes

    @classmethod
    def from_dto(cls, waiver: "dto.Waiver"):
        return cls(
            player=Player.from_dto(waiver.player),
            team=waiver.team.name,
            team_identity=TeamIdentity.bomzheg_engine_name,
            played=waiver.played,
        )


@dataclass
class GameStat:
    id: int
    start_at: datetime
    results: dict[str, list[LevelTime]]
    keys: dict[str, list[Key]]
    waivers: list[Waiver] = dataclasses.field(default_factory=list)
    team_identity: TeamIdentity = TeamIdentity.forum_name
