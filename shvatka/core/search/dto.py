import enum
from collections.abc import Sequence
from dataclasses import dataclass, field

from shvatka.core.models import dto
from shvatka.core.models.dto import action


@dataclass(frozen=True, kw_only=True)
class SearchFilters:
    """Где искать. По умолчанию — везде."""

    games: bool = True
    levels: bool = True
    teams: bool = True
    players: bool = True


@dataclass(frozen=True, kw_only=True)
class LevelWithGame:
    """Кандидат для поиска по уровням: уровень вместе с игрой, к которой он привязан."""

    level: dto.Level
    game: dto.Game


class LevelMatchField(enum.Enum):
    name_id = "name_id"
    hint = "hint"
    key = "key"


class PlayerMatchField(enum.Enum):
    username = "username"
    tg_username = "tg_username"
    tg_name = "tg_name"
    forum_name = "forum_name"


@dataclass(frozen=True, kw_only=True)
class GameHit:
    game: dto.Game
    snippet: str


@dataclass(frozen=True, kw_only=True)
class LevelHit:
    level: dto.Level
    game: dto.Game
    found_in: LevelMatchField
    snippet: str
    hint_number: int | None = None
    """Номер подсказки в списке подсказок уровня (с нуля)."""
    hint_time: int | None = None
    """Время выхода подсказки, минуты."""
    hint_part_number: int | None = None
    """Номер части внутри подсказки (с нуля)."""
    condition_key: Sequence[str] = ()
    """Ключи которые выводят такую подсказку"""
    condition_timer: int | None = None
    """Таймер в минутах"""
    key: action.SHKey | None = None


@dataclass(frozen=True, kw_only=True)
class TeamHit:
    team: dto.Team
    snippet: str


@dataclass(frozen=True, kw_only=True)
class PlayerHit:
    player: dto.Player
    found_in: PlayerMatchField
    snippet: str


@dataclass(frozen=True, kw_only=True)
class SearchResults:
    games: list[GameHit] = field(default_factory=list)
    levels: list[LevelHit] = field(default_factory=list)
    teams: list[TeamHit] = field(default_factory=list)
    players: list[PlayerHit] = field(default_factory=list)
