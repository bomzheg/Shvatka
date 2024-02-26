from aiogram import Bot
from aiogram_dialog.api.protocols import MessageManagerProtocol
from aiogram_dialog.test_tools import MockMessageManager
from aiogram_tests.mocked_bot import MockedBot
from dishka import Provider, provide, Scope

from shvatka.tgbot.config.models.main import TgBotConfig


class MockMessageManagerProvider(Provider):
    scope = Scope.APP

    @provide
    def get_manager(self) -> MessageManagerProtocol:
        return MockMessageManager()


class MockBotProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_bot(self, config: TgBotConfig) -> Bot:
        return MockedBot(token=config.bot.token)
