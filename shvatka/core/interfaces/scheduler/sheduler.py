from datetime import datetime
from typing import Protocol

from shvatka.core.models import dto


class Scheduler(Protocol):
    async def plain_prepare(self, game: dto.Game):
        raise NotImplementedError

    async def plain_start(self, game: dto.Game):
        raise NotImplementedError

    async def plain_hint(
        self,
        level: dto.Level,
        team: dto.Team,
        hint_number: int,
        run_at: datetime,
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
