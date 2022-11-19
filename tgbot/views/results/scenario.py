import asyncio
from _operator import add
from datetime import timedelta
from functools import reduce
from io import BytesIO

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.utils.text_decorations import html_decoration as hd
from telegraph.aio import Telegraph

from shvatka.models import dto
from shvatka.utils.datetime_utils import DATE_FORMAT
from tgbot.config.models.bot import BotConfig
from tgbot.views.hint_sender import HintSender
from tgbot.views.keys import render_log_keys
from tgbot.views.results.level_times import export_results


class GamePublisher:
    def __init__(
        self,
        hint_sender: HintSender,
        game: dto.FullGame,
        channel_id: int,
        bot: Bot,
        config: BotConfig,
        game_stat: dto.GameStat,
        telegraph: Telegraph,
        keys: dict[dto.Team, list[dto.KeyTime]],
    ):
        self.hint_sender = hint_sender
        self.game = game
        self.channel_id = channel_id
        self.bot = bot
        self.config = config
        self.game_stat = game_stat
        self.telegraph = telegraph
        self.keys = keys

    async def publish_scn(self) -> int:
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

    async def publish_results(self):
        file = BytesIO()
        await export_results(game=self.game, game_stat=self.game_stat, file=file)
        msg = await self.bot.send_document(
            chat_id=self.channel_id,
            document=BufferedInputFile(file=file.read(), filename=f"{self.game.name}.xlsx"),
        )
        file.close()
        return msg.message_id

    async def publish_keys(self) -> int:
        text = render_log_keys(self.keys)
        page = await self.telegraph.create_page(
            title=f"Лог ключей игры {self.game.name}",
            html_content=text,
        )
        msg = await self.bot.send_message(
            chat_id=self.channel_id,
            text=hd.link("Лог ключей игры", page["url"]),
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
