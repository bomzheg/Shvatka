import asyncio
import logging
from datetime import timedelta
from functools import partial
from typing import Iterable, Callable, Awaitable, Collection

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models import enums
from shvatka.core.models.dto import scn
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver

logger = logging.getLogger(__name__)
METHODS: dict[enums.HintType, Callable[..., Awaitable[Message]]] = {
    enums.HintType.text: Bot.send_message,
    enums.HintType.gps: Bot.send_location,
    enums.HintType.venue: Bot.send_venue,
    enums.HintType.photo: Bot.send_photo,
    enums.HintType.audio: Bot.send_audio,
    enums.HintType.video: Bot.send_video,
    enums.HintType.document: Bot.send_document,
    enums.HintType.animation: Bot.send_animation,
    enums.HintType.voice: Bot.send_voice,
    enums.HintType.video_note: Bot.send_video_note,
    enums.HintType.contact: Bot.send_contact,
    enums.HintType.sticker: Bot.send_sticker,
}


class HintSender:
    SLEEP: timedelta = timedelta(seconds=1)

    def __init__(self, bot: Bot, resolver: HintContentResolver):
        self.bot = bot
        self.resolver = resolver
        self.methods: dict[enums.HintType, Callable[..., Awaitable[Message]]] = {
            t: partial(m, bot) for t, m in METHODS.items()
        }

    def method(self, type_content: enums.HintType) -> Callable[..., Awaitable[Message]]:
        return self.methods[type_content]

    async def send_hint(self, hint_container: scn.BaseHint, chat_id: int) -> Message:
        method = self.method(enums.HintType[hint_container.type])
        hint_link = await self.resolver.resolve_link(hint_container)
        try:
            return await method(chat_id=chat_id, **hint_link.kwargs())
        except TelegramAPIError:
            logger.warning("cant send hint by file_id %s", hint_link)
            hint_content = await self.resolver.resolve_content(hint_container)
            return await method(chat_id=chat_id, **hint_content.kwargs())

    async def send_hints(
        self,
        chat_id: int,
        hint_containers: Iterable[scn.BaseHint],
        caption: str | None = None,
        sleep: int | None = None,
    ):
        """
        sending caption if exist and all hint parts in chat with chat_id
        :param chat_id:
        :param hint_containers:
        :param caption: this text may send before hints
        :param sleep:  time to sleep inter sending parts (default 1 sec)
        :return:
        """
        if sleep is None:
            sleep = self.SLEEP.seconds
        if caption is not None:
            await self.bot.send_message(chat_id=chat_id, text=caption)
            await asyncio.sleep(sleep)
        for hint_container in hint_containers:
            await self.send_hint(hint_container, chat_id)
            await asyncio.sleep(sleep)

    @classmethod
    def get_approximate_time(cls, hints: Collection[scn.BaseHint]) -> timedelta:
        approximate_io_time = timedelta(milliseconds=100)
        return len(hints) * cls.SLEEP + len(hints) * approximate_io_time


def create_hint_sender(bot: Bot, dao: HolderDao, storage: FileStorage) -> HintSender:
    return HintSender(
        bot=bot,
        resolver=HintContentResolver(dao=dao.file_info, file_storage=storage),
    )
