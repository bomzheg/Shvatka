from unittest import mock

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram_dialog.api.protocols import MessageManagerProtocol
from aiogram_dialog.test_tools import MockMessageManager
from dishka import Provider, provide, Scope

from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.views.bot_alert import BotAlert
from shvatka.tgbot.views.jinja_filters import setup_jinja


class MockMessageManagerProvider(Provider):
    scope = Scope.APP

    @provide
    def get_manager(self) -> MessageManagerProtocol:
        return MockMessageManager()


class MockBotProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_bot_session(self) -> BaseSession:
        session = mock.AsyncMock(BaseSession)
        return session

    @provide
    async def get_bot(self, config: TgBotConfig, session: BaseSession) -> Bot:
        bot = Bot(token=config.bot.token, session=session)
        setup_jinja(bot)
        return bot

    @provide
    async def bot_alert(self, bot: Bot, config: BotConfig) -> BotAlert:
        return BotAlert(bot, config.log_chat)
