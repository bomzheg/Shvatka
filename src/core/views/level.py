from typing import Protocol

from src.core.models import dto


class LevelView(Protocol):
    async def send_puzzle(self, suite: dto.LevelTestSuite) -> None:
        raise NotImplementedError

    async def send_hint(self, suite: dto.LevelTestSuite, hint_number: int) -> None:
        raise NotImplementedError

    async def correct_key(self, suite: dto.LevelTestSuite, key: str) -> None:
        raise NotImplementedError

    async def wrong_key(self, suite: dto.LevelTestSuite, key: str) -> None:
        raise NotImplementedError

    async def level_finished(self, suite: dto.LevelTestSuite) -> None:
        raise NotImplementedError
