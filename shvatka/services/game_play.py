import logging

from shvatka.dal.game_play import GamePreparer
from shvatka.models import dto
from shvatka.scheduler import ScheduledContext
from shvatka.views.game import GameViewPreparer

logger = logging.getLogger(__name__)


async def prepare_game(game: dto.Game, game_preparer: GamePreparer, view_preparer: GameViewPreparer):
    await game_preparer.delete_poll_data()
    await view_preparer.prepare_game_view(
        game=game,
        teams=await game_preparer.get_agree_teams(game),
        orgs=await game_preparer.get_orgs(game),
    )


async def start_game(game: dto.Game, context: ScheduledContext):
    await context.dao.game.start(game)
    logger.info("game %s started", game.id)
    await context.dao.commit()
