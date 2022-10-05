import asyncio
import logging

from shvatka.dal.game_play import GamePreparer
from shvatka.dal.level_times import GameStarter
from shvatka.models import dto
from shvatka.scheduler import Scheduler
from shvatka.views.game import GameViewPreparer, GameLogWriter, GameView

logger = logging.getLogger(__name__)


async def prepare_game(game: dto.Game, game_preparer: GamePreparer, view_preparer: GameViewPreparer):
    await game_preparer.delete_poll_data()
    await view_preparer.prepare_game_view(
        game=game,
        teams=await game_preparer.get_agree_teams(game),
        orgs=await game_preparer.get_orgs(game),
    )


async def start_game(game: dto.Game, dao: GameStarter, game_log: GameLogWriter, view: GameView, scheduler: Scheduler):
    await dao.set_game_started(game)
    logger.info("game %s started", game.id)

    teams = await dao.get_played_teams(game)

    await dao.set_teams_to_first_level(game, teams)

    puzzle = await dao.get_puzzle(game, 0)
    await asyncio.gather(*[view.send_puzzle(team, puzzle) for team in teams])

    hint = await dao.get_next_hint(game, 0, 0)
    await asyncio.gather(*[scheduler.plain_hint(game, team, 0, hint) for team in teams])

    await dao.commit()
    await game_log.log("Game started")
