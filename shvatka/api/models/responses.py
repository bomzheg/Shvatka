import typing
from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence, Generic

from shvatka.core.games.dto import CurrentHints
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import scn
from shvatka.core.models.enums import GameStatus

T = typing.TypeVar("T")


@dataclass
class Page(Generic[T]):
    content: Sequence[T]


@dataclass
class Player:
    id: int
    can_be_author: bool
    name_mention: str

    @classmethod
    def from_core(cls, core: dto.Player):
        return cls(
            id=core.id,
            can_be_author=core.can_be_author,
            name_mention=core.name_mention,
        )


@dataclass
class Team:
    id: int
    name: str
    captain: Player | None
    description: str | None

    @classmethod
    def from_core(cls, core: dto.Team):
        return cls(
            id=core.id,
            name=core.name,
            captain=Player.from_core(core.captain) if core.captain else None,
            description=core.description,
        )


@dataclass
class Game:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None = None
    number: int | None = None

    @classmethod
    def from_core(cls, core: dto.Game | None):
        if core is None:
            return None
        return cls(
            id=core.id,
            author=Player.from_core(core.author),
            name=core.name,
            status=core.status,
            start_at=core.start_at,
            number=core.number,
        )


@dataclass
class Level:
    db_id: int
    name_id: str
    author: Player
    scenario: scn.LevelScenario
    game_id: int | None = None
    number_in_game: int | None = None

    @classmethod
    def from_core(cls, core: dto.Level | None = None):
        if core is None:
            return None
        return cls(
            db_id=core.db_id,
            name_id=core.name_id,
            author=Player.from_core(core.author),
            scenario=core.scenario,
            game_id=core.game_id,
            number_in_game=core.number_in_game,
        )


@dataclass
class FullGame:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None
    levels: list[Level] = field(default_factory=list)

    @classmethod
    def from_core(cls, core: dto.FullGame | None = None):
        if core is None:
            return None
        return cls(
            id=core.id,
            author=Player.from_core(core.author),
            name=core.name,
            status=core.status,
            start_at=core.start_at,
            levels=[Level.from_core(level) for level in core.levels],
        )


@dataclass(frozen=True)
class KeyTime:
    text: str
    type_: enums.KeyType
    is_duplicate: bool
    at: datetime
    level_number: int
    player: Player
    team: Team

    @classmethod
    def from_core(cls, core: dto.KeyTime | None):
        if core is None:
            return None
        return cls(
            text=core.text,
            type_=core.type_,
            is_duplicate=core.is_duplicate,
            at=core.at,
            level_number=core.level_number,
            player=Player.from_core(core.player),
            team=Team.from_core(core.team),
        )


@dataclass
class LevelTime:
    id: int
    team: Team
    level_number: int
    start_at: datetime
    is_finished: bool

    @classmethod
    def from_core(cls, core: dto.LevelTimeOnGame | None):
        if core is None:
            return None
        return cls(
            id=core.id,
            team=Team.from_core(core.team),
            level_number=core.level_number,
            start_at=core.start_at,
            is_finished=core.is_finished,
        )


@dataclass
class GameStat:
    level_times: dict[int, list[LevelTime]]

    @classmethod
    def from_core(cls, core: dto.GameStat | None):
        if core is None:
            return None
        return cls(
            level_times={
                team.id: [LevelTime.from_core(lt) for lt in lts]
                for team, lts in core.level_times.items()
            },
        )


@dataclass
class CurrentHintResponse:
    hints: list[scn.TimeHint]
    typed_keys: list[KeyTime]
    level_number: int
    started_at: datetime

    @classmethod
    def from_core(cls, core: CurrentHints):
        if core is None:
            return None
        return cls(
            hints=core.hints,
            typed_keys=[KeyTime.from_core(kt) for kt in core.typed_keys],
            level_number=core.level_number,
            started_at=core.started_at,
        )
