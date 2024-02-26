from aiogram import Bot
from aiogram.enums import ParseMode
from dishka import Provider, Scope, provide

from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.jinja_filters import setup_jinja


class BotProvider(Provider):
    scope = Scope.APP

    @provide
    def get_bot(self, config: BotConfig) -> Bot:
        bot = Bot(
            token=config.token,
            parse_mode=ParseMode.HTML,
            session=config.create_session(),
        )
        setup_jinja(bot)
        return bot
