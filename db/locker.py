import asyncio

from shvatka.models import dto
from shvatka.utils.key_checker_lock import KeyCheckerLock, KeyCheckerFactory


class MemoryLock(KeyCheckerLock):
    def __init__(self):
        self._lock = asyncio.Lock()

    async def acquire(self):
        await self._lock.acquire()

    async def release(self):
        self._lock.release()


class MemoryLockFactory(KeyCheckerFactory):
    def __init__(self):
        self.locks: dict[int, MemoryLock] = {}

    def lock(self, team: dto.Team) -> KeyCheckerLock:
        return self.locks.setdefault(team.id, MemoryLock())

    def clear(self):
        self.locks.clear()
