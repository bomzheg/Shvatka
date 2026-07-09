import logging
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Protocol

from aiogram import Bot

from shvatka.core.interfaces.bus import ActionRequestResolved, Bus, Event, OneTimeTokenUsed
from shvatka.tgbot.views.utils import total_remove_msg

logger = logging.getLogger(__name__)


class UsedOneTimeTokenInteractor(Protocol, metaclass=ABCMeta):
    @abstractmethod
    async def __call__(self, player_id):
        pass


@dataclass(kw_only=True)
class InMemoryBus(Bus):
    one_time_token: UsedOneTimeTokenInteractor
    bot: Bot

    async def submit(self, event: Event) -> None:
        try:
            match event:
                case OneTimeTokenUsed(player_id=player_id):
                    await self.one_time_token(player_id=player_id)
                case ActionRequestResolved(bot_messages=bot_messages):
                    for bot_message in bot_messages:
                        await total_remove_msg(
                            self.bot,
                            chat_id=bot_message["chat_id"],
                            msg_id=bot_message["message_id"],
                        )
        except Exception as e:
            logger.error("error while processing event %s", event, exc_info=e)
