import asyncio
from typing import Iterable, Callable, Awaitable

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from shvatka.models.dto.scn.hint_part import BaseHint
from shvatka.models.enums.hint_type import HintType
from tgbot.views.hint_content_resolver import HintContentResolver


class HintSender:
    def __init__(self, bot: Bot, resolver: HintContentResolver):
        self.bot = bot
        self.resolver = resolver
        self.methods = {
            HintType.text: self.bot.send_message,
            HintType.gps: self.bot.send_location,
            HintType.venue: self.bot.send_venue,
            HintType.photo: self.bot.send_photo,
            HintType.audio: self.bot.send_audio,
            HintType.video: self.bot.send_video,
            HintType.document: self.bot.send_document,
            HintType.animation: self.bot.send_animation,
            HintType.voice: self.bot.send_voice,
            HintType.video_note: self.bot.send_video_note,
            HintType.contact: self.bot.send_contact,
            HintType.sticker: self.bot.send_sticker,
        }

    def method(self, type_content: HintType) -> Callable[..., Awaitable[Message]]:
        return self.methods[type_content]

    async def send_hint(self, hint_container: BaseHint, chat_id: int) -> Message:
        method = self.method(HintType[hint_container.type])
        try:
            hint_link = await self.resolver.resolve_link(hint_container)
            return await method(chat_id=chat_id, **hint_link.kwargs())
        except TelegramAPIError:
            hint_content = await self.resolver.resolve_content(hint_container)
            return await method(chat_id=chat_id, **hint_content.kwargs())

    async def send_hints(
        self,
        chat_id: int,
        hint_containers: Iterable[BaseHint],
        caption: str | None = None,
        sleep: int = 1
    ):
        """
        sending caption if exist and all hint parts in chat with chat_id
        :param chat_id:
        :param hint_containers:
        :param caption: this text may send before hints
        :param sleep:  time to sleep inter sending parts
        :return:
        """
        if caption is not None:
            await self.bot.send_message(chat_id=chat_id, text=caption)
            await asyncio.sleep(sleep)
        for hint_container in hint_containers:
            await self.send_hint(hint_container, chat_id)
            await asyncio.sleep(sleep)
