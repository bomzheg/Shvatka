import asyncio
import logging
from datetime import timedelta
from functools import reduce
from operator import add
from typing import Iterable, Callable, Awaitable, Collection

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration as hd

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.models.dto.scn.hint_part import BaseHint
from shvatka.models.enums.hint_type import HintType
from shvatka.utils.datetime_utils import DATE_FORMAT
from tgbot.config.models.bot import BotConfig
from tgbot.views.hint_factory.hint_content_resolver import HintContentResolver

logger = logging.getLogger(__name__)


class HintSender:
    SLEEP: timedelta = timedelta(seconds=1)

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
        hint_containers: Iterable[BaseHint],
        caption: str | None = None,
        sleep: int = None
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
    def get_approximate_time(cls, hints: Collection[BaseHint]) -> timedelta:
        approximate_io_time = timedelta(milliseconds=100)
        return len(hints) * cls.SLEEP + len(hints) * approximate_io_time


class GamePublisher:
    def __init__(self, hint_sender: HintSender, game: dto.FullGame, channel_id: int, bot: Bot, config: BotConfig):
        self.hint_sender = hint_sender
        self.game = game
        self.channel_id = channel_id
        self.bot = bot
        self.config = config

    async def publish(self) -> int:
        msg = await self.bot.send_message(
            chat_id=self.channel_id,
            text=f"Сценарий игры {hd.quote(self.game.name)} "
                 f"({self.game.start_at.strftime(DATE_FORMAT)})",
        )
        for level in self.game.levels:
            level_publisher = LevelPublisher(
                hint_sender=self.hint_sender,
                level=level,
                channel_id=self.channel_id,
            )
            await level_publisher.publish()
        await self.bot.send_message(
            chat_id=self.channel_id,
            text="Это был весь сценарий игры",
        )
        return msg.message_id

    def get_approximate_time(self) -> timedelta:
        return reduce(add, (LevelPublisher.get_approximate_time(level) for level in self.game.levels))


class LevelPublisher:
    SLEEP: timedelta = timedelta(seconds=10)

    def __init__(self, hint_sender: HintSender, level: dto.Level, channel_id: int):
        self.hint_sender = hint_sender
        self.level = level
        self.channel_id = channel_id

    async def publish(self):
        for hint_number, hint in enumerate(self.level.scenario.time_hints):
            if hint.time == 0:
                text = f"🔒 <b>Уровень № {self.level.number_in_game + 1}</b>\n" \
                       f"Ключи уровня:\n🔑 " + '\n🔑 '.join(self.level.scenario.keys)
            elif hint_number == len(self.level.scenario.time_hints) - 1:
                text = f"🔖 Последняя подсказка уровня №{self.level.number_in_game + 1} ({hint.time} мин.):\n"
            else:
                text = f"🔖 Уровень №{self.level.number_in_game + 1}. Подсказка №{hint_number} ({hint.time} мин.):\n"
            await asyncio.sleep(self.SLEEP.seconds)
            await self.hint_sender.send_hints(self.channel_id, hint.hint, text)

    @classmethod
    def get_approximate_time(cls, level: dto.Level) -> timedelta:
        return len(level.scenario.time_hints) * cls.SLEEP + reduce(add, (
            HintSender.get_approximate_time(hints.hint) for hints in level.scenario.time_hints
        ))


def create_hint_sender(bot: Bot, dao: HolderDao, storage: FileStorage) -> HintSender:
    return HintSender(
        bot=bot,
        resolver=HintContentResolver(dao=dao.file_info, file_storage=storage),
    )
