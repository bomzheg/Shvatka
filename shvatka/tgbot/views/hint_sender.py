import asyncio
import logging
from datetime import timedelta
from functools import partial
from typing import Iterable, Callable, Awaitable, Collection

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

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
        file_info_dao: FileInfoDao,
    ) -> None:
        self.bot = bot
        self.resolver = resolver
        # dedicated dao (its own session/transaction) used to persist a fresh
        # file_id after sending by content, independently of the request's tx
        self.file_info_dao = file_info_dao
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
            except TelegramAPIError as e:
                logger.warning("cant send hint by file_id %s", hint_link, exc_info=e)
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
            if tg_link is None or tg_link.file_id is None:
                return
            await self.file_info_dao.update_file_id(guid, tg_link.file_id)
            await self.file_info_dao.commit()
        except Exception as e:
            # renewing file_id is best-effort and must never break sending
            logger.error("cant renew file_id for hint with guid %s", guid, exc_info=e)

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


def _is_file_id_missing(hint_link: object) -> bool:
    """
    Only file-based link views (photo, audio, video, ...) carry a ``file_id``
    attribute. When that attribute exists but is ``None`` the file was never
    uploaded to telegram, so we can't send by file_id and must fall back to
    sending by content.

    Views without a ``file_id`` attribute at all (text, gps, venue, contact)
    have nothing to be missing - they are always sendable as a link, so the
    sentinel default keeps them out of the content fallback.
    """
    return getattr(hint_link, "file_id", _MISSING) is None
