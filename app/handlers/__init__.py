import logging

from aiogram import Dispatcher

from app.handlers import base, game
from app.handlers import errors
from app.handlers import last
from app.handlers import superuser
from app.handlers import team
from app.models.config.main import BotConfig

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
