import logging
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Protocol

from shvatka.core.interfaces.bus import Bus, Event, OneTimeTokenUsed

logger = logging.getLogger(__name__)


class UsedOneTimeTokenInteractor(Protocol, metaclass=ABCMeta):
    @abstractmethod
    async def __call__(self, player_id):
        pass


@dataclass(kw_only=True)
class InMemoryBus(Bus):
    one_time_token: UsedOneTimeTokenInteractor

    async def submit(self, event: Event) -> None:
        try:
            match event:
                case OneTimeTokenUsed(player_id=player_id):
                    await self.one_time_token(player_id=player_id)
        except Exception as e:
            logger.error("error while processing event %s", event, exc_info=e)
