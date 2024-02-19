from aiogram import Bot
from dishka import Provider, Scope, provide

from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.main_factory import create_bot


class BotProvider(Provider):
    scope = Scope.APP

    @provide
    def get_bot(self, config: BotConfig) -> Bot:
        return create_bot(config)
