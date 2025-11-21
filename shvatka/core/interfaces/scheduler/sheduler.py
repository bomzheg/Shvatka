from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Protocol

from shvatka.core.models import dto
from shvatka.core.models.dto import action


class Scheduler(Protocol, metaclass=ABCMeta):
    async def plain_prepare(self, game: dto.Game):
        raise NotImplementedError

    async def plain_start(self, game: dto.Game):
        raise NotImplementedError

    async def plain_hint(
        self,
        level: dto.Level,
        team: dto.Team,
        hint_number: int,
        lt_id: int,
        run_at: datetime,
    ):
        raise NotImplementedError

    @abstractmethod
    async def plain_level_event(
        self, team: dto.Team, lt_id: int, effects: action.Effects, run_at: datetime
    ):
        raise NotImplementedError

    async def cancel_scheduled_game(self, game: dto.Game):
        raise NotImplementedError

    async def start(self):
        raise NotImplementedError

    async def close(self):
        raise NotImplementedError

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class LevelTestScheduler(Protocol):
    async def plain_test_hint(
        self,
        suite: dto.LevelTestSuite,
        hint_number: int,
        run_at: datetime,
    ):
        raise NotImplementedError
