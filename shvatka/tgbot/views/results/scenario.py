import asyncio
from _operator import add
from datetime import timedelta
from functools import reduce
from io import BytesIO

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.utils.text_decorations import html_decoration as hd
from telegraph.aio import Telegraph

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import DATE_FORMAT
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.dialogs.level_scn import effects_key_dialog
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.keys import (
    render_log_keys,
    render_win_key_condition,
)
from shvatka.tgbot.views.level import (
    render_effects_key_caption,
    render_effects_timer_caption,
)
from shvatka.tgbot.views.results.level_times import export_results


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
    ) -> None:
        self.hint_sender = hint_sender
        self.game = game
        self.channel_id = channel_id
        self.bot = bot
        self.config = config
        self.game_stat = game_stat
        self.telegraph = telegraph
        self.keys = keys

    async def publish_scn(self) -> int:
        assert self.game.start_at is not None
        msg = await self.bot.send_message(
            chat_id=self.channel_id,
            text=f"Сценарий игры {hd.quote(self.game.name)} "
            f"({self.game.start_at.strftime(DATE_FORMAT)})",
        )
        for level in self.game.levels:
            level_publisher = LevelPublisher(
                hint_sender=self.hint_sender,
                level=level,
                chat_id=self.channel_id,
            )
            await level_publisher.publish()
        await self.bot.send_message(
            chat_id=self.channel_id,
            text="Это был весь сценарий игры",
        )
        return msg.message_id

    async def publish_results(self):
        file = BytesIO()
        export_results(game=self.game, game_stat=self.game_stat, file=file)
        file.seek(0)
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
        return reduce(
            add, (LevelPublisher.get_approximate_time(level) for level in self.game.levels)
        )


class LevelPublisher:
    SLEEP: timedelta = timedelta(seconds=2)

    def __init__(self, hint_sender: HintSender, level: dto.Level, chat_id: int) -> None:
        self.hint_sender = hint_sender
        self.level = level
        self.chat_id = chat_id

    async def publish(self):
        await self.publish_caption()
        await asyncio.sleep(self.SLEEP.seconds)
        await self.publish_effects_key()
        await asyncio.sleep(self.SLEEP.seconds)
        await self.publish_effects_timer()
        await asyncio.sleep(self.SLEEP.seconds)
        await self.publish_hints()

    async def publish_caption(self):
        text = f"🔒 {self.get_full_level_name()}\n"
        if default_keys := self.level.scenario.conditions.get_default_key_conditions():
            text += "Ключи уровня:\n"
            for c in default_keys:
                text += render_win_key_condition(c)
        else:
            text += "Не имеет ключей уровня."
        await self.send_message(text)

    async def publish_effects_key(self):
        if effect_keys := self.level.scenario.conditions.get_effects_key_conditions():
            await self.send_message("Ключи с эффектами:")
            for effect_key in effect_keys:
                await asyncio.sleep(self.SLEEP.seconds)
                caption, hints_ = render_effects_key_caption(effect_key)
                await self.hint_sender.send_hints(
                    chat_id=self.chat_id,
                    hint_containers=hints_,
                    caption=caption,
                )
        else:
            await self.send_message("Не имеет ключей с эффектами")

    async def publish_effects_timer(self):
        if effect_timers := self.level.scenario.conditions.get_effects_timer_conditions():
            await self.send_message("Таймеры:")
            for timer in effect_timers:
                caption, hints_ = render_effects_timer_caption(timer)
                await asyncio.sleep(self.SLEEP.seconds)
                await self.hint_sender.send_hints(
                    chat_id=self.chat_id,
                    hint_containers=hints_,
                    caption=caption,
                )
        else:
            await self.send_message("Не имеет таймеров")

    async def publish_hints(self):
        for hint_number, hint in enumerate(self.level.scenario.time_hints):
            if hint.time == 0:
                text = f"🔒 {self.get_full_level_name()}:\n"
            elif hint_number == len(self.level.scenario.time_hints) - 1:
                text = (
                    f"🔖 Последняя подсказка уровня {self.get_level_name()} "
                    f"({hint.time} мин.):\n"
                )
            else:
                text = (
                    f"🔖 Уровень №{self.get_level_name()}. "
                    f"Подсказка №{hint_number} ({hint.time} мин.):\n"
                )
            await asyncio.sleep(self.SLEEP.seconds)
            await self.hint_sender.send_hints(self.chat_id, hint.hint, text)

    async def send_message(self, text: str) -> None:
        await self.hint_sender.bot.send_message(self.chat_id, text)

    def get_level_name(self) -> str:
        if self.level.number_in_game:
            return self._level_number()
        else:
            return self._level_name_id()

    def get_full_level_name(self) -> str:
        if self.level.number_in_game:
            return f"<b>Уровень {self._level_number()}</b> ({self._level_name_id()})"
        else:
            return f"<b>Уровень {self._level_name_id()}</b>"

    def _level_number(self) -> str:
        return f"№ {self.level.number_in_game + 1}"

    def _level_name_id(self) -> str:
        return f"({hd.quote(self.level.name_id)})"

    @classmethod
    def get_approximate_time(cls, level: dto.Level) -> timedelta:
        captions_time = level.hints_count * cls.SLEEP + 3 * cls.SLEEP
        effects_keys_captions = len(level.scenario.conditions.get_effects_key_conditions()) * cls.SLEEP
        effects_timers_captions = len(level.scenario.conditions.get_effects_timer_conditions()) * cls.SLEEP
        time_tints_time = reduce(
            add,
            (HintSender.get_approximate_time(hints.hint) for hints in level.scenario.time_hints),
        )
        bonus_hints_time = HintSender.get_approximate_time(level.scenario.conditions.get_hints())
        return captions_time + time_tints_time + bonus_hints_time + effects_keys_captions + effects_timers_captions
