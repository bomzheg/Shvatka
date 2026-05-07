from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Protocol

from shvatka.core.interfaces.bus import Bus, Event, OneTimeTokenUsed


class UsedOneTimeTokenInteractor(Protocol, metaclass=ABCMeta):
    @abstractmethod
    async def __call__(self, player_id):
        pass


@dataclass(kw_only=True)
class InMemoryBus(Bus):
    one_time_token: UsedOneTimeTokenInteractor

    async def submit(self, evet: Event) -> None:
        match evet:
            case OneTimeTokenUsed(player_id=player_id):
                await self.one_time_token(player_id=player_id)
