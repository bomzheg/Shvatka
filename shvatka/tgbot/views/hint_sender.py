import asyncio
import logging
from datetime import timedelta
from functools import partial
from typing import Iterable, Callable, Awaitable, Collection

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shvatka.core.models import enums
from shvatka.core.models.dto import hints
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_factory.hint_parser import parse_message

logger = logging.getLogger(__name__)

_MISSING = object()
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

    def __init__(
        self,
        bot: Bot,
        resolver: HintContentResolver,
        pool: async_sessionmaker[AsyncSession],
    ) -> None:
        self.bot = bot
        self.resolver = resolver
        self.pool = pool
        self.methods: dict[enums.HintType, Callable[..., Awaitable[Message]]] = {
            t: partial(m, bot) for t, m in METHODS.items()
        }

    def method(self, type_content: enums.HintType) -> Callable[..., Awaitable[Message]]:
        return self.methods[type_content]

    async def send_hint(self, hint_container: hints.BaseHint, chat_id: int) -> Message:
        method = self.method(enums.HintType[hint_container.type])
        hint_link = await self.resolver.resolve_link(hint_container)
        if _is_file_id_missing(hint_link):
            logger.warning("hint has no file_id, sending by content: %s", hint_link)
        else:
            try:
                return await method(chat_id=chat_id, **hint_link.kwargs())
            except TelegramAPIError:
                logger.warning("cant send hint by file_id %s", hint_link)
        return await self._send_by_content(method, hint_container, chat_id)

    async def _send_by_content(
        self,
        method: Callable[..., Awaitable[Message]],
        hint_container: hints.BaseHint,
        chat_id: int,
    ) -> Message:
        hint_content = await self.resolver.resolve_content(hint_container)
        message = await method(chat_id=chat_id, **hint_content.kwargs())
        await self._renew_file_id(hint_container, message)
        return message

    async def _renew_file_id(self, hint_container: hints.BaseHint, message: Message) -> None:
        """
        After a hint was sent by content telegram returns a fresh file_id.
        Persist it in a dedicated session (separate transaction) so that
        the next time the hint can be sent by file_id again.

        This is best-effort: the hint is already delivered, so a failure to
        renew the file_id must not propagate.
        """
        guid = getattr(hint_container, "file_guid", None)
        if guid is None:
            return
        try:
            tg_link = parse_message(message)
            if tg_link is None:
                return
            async with self.pool() as session:
                dao = FileInfoDao(session)
                await dao.update_file_id(guid, tg_link.file_id)
                await dao.commit()
        except Exception:
            # renewing file_id is best-effort and must never break sending
            logger.exception("cant renew file_id for hint with guid %s", guid)

    async def send_hints(
        self,
        chat_id: int,
        hint_containers: Iterable[hints.BaseHint],
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
    def get_approximate_time(cls, hints: Collection[hints.BaseHint]) -> timedelta:
        approximate_io_time = timedelta(milliseconds=100)
        return len(hints) * cls.SLEEP + len(hints) * approximate_io_time


def _is_file_id_missing(hint_link: hints.BaseHint | object) -> bool:
    """
    File-based link views carry a ``file_id`` attribute. When it is ``None``
    (e.g. it was never uploaded to telegram) we can't send by file_id and
    have to fall back to sending by content. Views without a ``file_id``
    (text, gps, venue, contact) are always sendable as a link.
    """
    return getattr(hint_link, "file_id", _MISSING) is None
