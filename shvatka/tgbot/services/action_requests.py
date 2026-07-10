from dataclasses import dataclass

from aiogram import Bot

from shvatka.core.notifications.adapters import RequestStorage
from shvatka.infrastructure.bus.in_memory import ActionResolvedInteractor
from shvatka.tgbot.views.utils import total_remove_msg


@dataclass
class ActionResolvedInteractorImpl(ActionResolvedInteractor):
    bot: Bot
    requests: RequestStorage

    async def __call__(self, request_id: int) -> None:
        bot_messages = await self.requests.get_bot_messages(request_id)
        for chat_id, message_id in bot_messages:
            await total_remove_msg(
                self.bot,
                chat_id=chat_id,
                msg_id=message_id,
            )
