from typing import AsyncIterable

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import Provider, Scope, provide

from shvatka.core.views.game import GameLogWriter
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.game import GameBotLog
from shvatka.tgbot.views.jinja_filters import setup_jinja


class BotProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_bot(self, config: BotConfig) -> AsyncIterable[Bot]:
        async with Bot(
            token=config.token,
            session=config.create_session(),
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                allow_sending_without_reply=True,
            ),
        ) as bot:
            setup_jinja(bot)
            yield bot


class GameLogProvider(Provider):
    scope = Scope.APP

    @provide
    def get_game_log(self, bot: Bot, config: BotConfig) -> GameLogWriter:
        return GameBotLog(bot=bot, log_chat_id=config.game_log_chat)
