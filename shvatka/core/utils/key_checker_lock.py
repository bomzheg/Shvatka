from typing import Protocol

from shvatka.core.models import dto


class KeyCheckerLock(Protocol):
    async def acquire(self):
        raise NotImplementedError

    async def release(self):
        raise NotImplementedError

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()


class KeyCheckerFactory(Protocol):
    def lock_team(self, team: dto.Team) -> KeyCheckerLock:
        raise NotImplementedError

    def lock_player(self, player: dto.Player) -> KeyCheckerLock:
        raise NotImplementedError

    def lock_globally(self) -> KeyCheckerLock:
        raise NotImplementedError

    def __call__(self, team: dto.Team) -> KeyCheckerLock:
        return self.lock_team(team)

    def clear(self) -> None:
        raise NotImplementedError
