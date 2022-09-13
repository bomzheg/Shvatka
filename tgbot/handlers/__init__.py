import logging

from aiogram import Dispatcher

from shvatka.models.config.main import BotConfig
from tgbot.handlers import base, game
from tgbot.handlers import errors
from tgbot.handlers import last
from tgbot.handlers import superuser
from tgbot.handlers import team

logger = logging.getLogger(__name__)


def setup_handlers(dp: Dispatcher, bot_config: BotConfig):
    errors.setup(dp, bot_config.log_chat)
    base.setup(dp)
    superuser.setup(dp, bot_config)
    team.setup(dp)
    game.setup(dp)

    # always must be last registered
    last.setup(dp)
    logger.debug("handlers configured successfully")
