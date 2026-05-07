from dataclasses import dataclass
from typing import Protocol


@dataclass(kw_only=True, frozen=True, slots=True)
class Event:
    pass


@dataclass(kw_only=True, frozen=True, slots=True)
class OneTimeTokenUsed(Event):
    player_id: int


class Bus(Protocol):
    async def submit(self, evet: Event) -> None:
        pass
