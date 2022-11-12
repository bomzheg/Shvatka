from typing import Protocol

from shvatka.models import dto
from shvatka.models.dto.scn import TimeHint


class LevelView(Protocol):
    async def send_puzzle(self, tester: dto.Organizer, puzzle: TimeHint, level: dto.Level) -> None:
        raise NotImplementedError

    async def send_hint(self, tester: dto.Organizer, hint_number: int, level: dto.Level) -> None:
        raise NotImplementedError

    async def duplicate_key(self, tester: dto.Organizer, key: str) -> None:
        raise NotImplementedError

    async def correct_key(self, tester: dto.Organizer, key: str) -> None:
        raise NotImplementedError

    async def wrong_key(self, tester: dto.Organizer, key: str) -> None:
        raise NotImplementedError

    async def level_finished(self, tester: dto.Organizer) -> None:
        raise NotImplementedError
