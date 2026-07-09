from dataclasses import dataclass
from typing import Protocol


@dataclass(kw_only=True, frozen=True, slots=True)
class Event:
    pass


@dataclass(kw_only=True, frozen=True, slots=True)
class OneTimeTokenUsed(Event):
    player_id: int


@dataclass(kw_only=True, frozen=True, slots=True)
class ActionRequestResolved(Event):
    request_id: int
    bot_messages: tuple[dict[str, int], ...]


class Bus(Protocol):
    async def submit(self, event: Event) -> None:
        pass
