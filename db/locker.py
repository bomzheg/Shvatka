import asyncio

from shvatka.models import dto
from shvatka.utils.key_checker_lock import KeyCheckerLock, KeyCheckerFactory


class MemoryLock(KeyCheckerLock):
    def __init__(self):
        self.lock = asyncio.Lock()

    async def acquire(self):
        await self.lock.acquire()

    async def release(self):
        self.lock.release()


class MemoryLockFactory(KeyCheckerFactory):
    def __init__(self):
        self.locks: dict[int, MemoryLock] = {}

    def lock(self, team: dto.Team) -> KeyCheckerLock:
        return self.locks.setdefault(team.id, MemoryLock())

    def clear(self):
        self.locks.clear()
