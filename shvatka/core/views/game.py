from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Protocol, Iterable, Sequence, Any

from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.models import dto


class GameViewPreparer(Protocol):
    async def prepare_game_view(
        self,
        game: dto.Game,
        teams: Iterable[dto.Team],
        orgs: Iterable[dto.Organizer],
        dao: GamePreparer,
    ) -> None:
        raise NotImplementedError


class GameView(Protocol):
    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        raise NotImplementedError

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        raise NotImplementedError

    async def duplicate_key(self, key: dto.KeyTime) -> None:
        raise NotImplementedError

    async def correct_key(self, key: dto.KeyTime) -> None:
        raise NotImplementedError

    async def wrong_key(self, key: dto.KeyTime) -> None:
        raise NotImplementedError

    async def bonus_key(self, key: dto.KeyTime, bonus: float) -> None:
        raise NotImplementedError

    async def game_finished(self, team: dto.Team) -> None:
        raise NotImplementedError

    async def game_finished_by_all(self, team: dto.Team) -> None:
        raise NotImplementedError


class GameLogWriter(Protocol):
    async def log(self, log_event: GameLogEvent) -> None:
        raise NotImplementedError


class GameLogType(enum.Enum):
    GAME_WAIVERS_STARTED = enum.auto()
    GAME_PLANED = enum.auto()
    GAME_STARTED = enum.auto()
    GAME_FINISHED = enum.auto()
    TEAMS_MERGED = enum.auto()
    PLAYERS_MERGED = enum.auto()
    TEAM_CREATED = enum.auto()


@dataclass
class GameLogEvent:
    type: GameLogType
    data: dict[str, Any] = field(default_factory=dict)


class OrgNotifier(Protocol):
    async def notify(self, event: Event) -> None:
        raise NotImplementedError


@dataclass
class Event:
    orgs_list: Sequence[dto.Organizer]


@dataclass
class LevelUp(Event):
    team: dto.Team
    new_level: dto.Level


@dataclass
class NewOrg(Event):
    game: dto.Game
    org: dto.SecondaryOrganizer


@dataclass
class LevelTestCompleted(Event):
    suite: dto.LevelTestSuite
    result: dto.LevelTestingResult
