from typing import Protocol

from shvatka.models import dto


class Scheduler(Protocol):
    async def plain_prepare(self, game: dto.Game): pass

    async def plain_start(self, game: dto.Game): pass
