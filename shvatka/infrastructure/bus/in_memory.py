import logging
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Protocol


from shvatka.core.interfaces.bus import ActionRequestResolved, Bus, Event, OneTimeTokenUsed

logger = logging.getLogger(__name__)


class UsedOneTimeTokenInteractor(Protocol, metaclass=ABCMeta):
    @abstractmethod
    async def __call__(self, player_id: int) -> None:
        pass


class ActionResolvedInteractor(Protocol, metaclass=ABCMeta):
    @abstractmethod
    async def __call__(self, request_id: int) -> None:
        pass


@dataclass(kw_only=True)
class InMemoryBus(Bus):
    one_time_token: UsedOneTimeTokenInteractor
    action_resolved: ActionResolvedInteractor

    async def submit(self, event: Event) -> None:
        try:
            match event:
                case OneTimeTokenUsed(player_id=player_id):
                    await self.one_time_token(player_id=player_id)
                case ActionRequestResolved(request_id=request_id):
                    await self.action_resolved(request_id=request_id)
        except Exception as e:
            logger.error("error while processing event %s", event, exc_info=e)
