from typing import Protocol

from shvatka.models import dto
from shvatka.models.dto.scn.time_hint import TimeHint


class Scheduler(Protocol):
    async def plain_prepare(self, game: dto.Game):
        raise NotImplementedError

    async def plain_start(self, game: dto.Game):
        raise NotImplementedError

    async def plain_hint(self, game: dto.Game, team: dto.Team, level: int, hint: TimeHint):
        raise NotImplementedError
