import logging

from shvatka.models import dto
from shvatka.scheduler import ScheduledContext

logger = logging.getLogger(__name__)


async def prepare_game(game: dto.Game, context: ScheduledContext):
    await context.dao.poll.delete_all()


async def start_game(game: dto.Game, context: ScheduledContext):
    await context.dao.game.start(game)
    logger.info("game %s started", game.id)
    await context.dao.commit()
