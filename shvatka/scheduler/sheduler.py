from datetime import datetime
from typing import Protocol

from shvatka.models import dto


class Scheduler(Protocol):
    async def plain_prepare(self, game: dto.Game):
        raise NotImplementedError

    async def plain_start(self, game: dto.Game):
        raise NotImplementedError

    async def plain_hint(self, level: dto.Level, team: dto.Team, hint_number: int, run_at: datetime):
        raise NotImplementedError
