from datetime import datetime

from adaptix import Retort
from dishka.integrations.base import FromDishka

from shvatka.core.games.game_play import send_hint, start_game, prepare_game
from shvatka.core.games.interactors import GamePlayTimerInteractor
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models.dto import action
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.views.game import GameViewPreparer, GameView, GameLogWriter
from shvatka.core.views.level import LevelView
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.scheduler import SchedulerContainer
from shvatka.infrastructure.scheduler.context import inject
from shvatka.core.interfaces.scheduler import LevelTestScheduler, Scheduler
from shvatka.core.models import dto
from shvatka.core.services.level_testing import send_testing_level_hint
from shvatka.core.services.organizers import get_by_player
from shvatka.tgbot.views.bot_alert import BotAlert


@inject
async def prepare_game_wrapper(
    game_id: int,
    author_id: int,
    dao: FromDishka[HolderDao],
    view_preparer: FromDishka[GameViewPreparer],
) -> None:
    author = await dao.player.get_by_id(author_id)
    game = await dao.game.get_by_id(game_id, author)
    await prepare_game(
        game=game,
        game_preparer=dao.game_preparer,
        view_preparer=view_preparer,
    )


@inject
async def start_game_wrapper(
    game_id: int,
    author_id: int,
    dao: FromDishka[HolderDao],
    scheduler: FromDishka[Scheduler],
    game_view: FromDishka[GameView],
    game_log_writer: FromDishka[GameLogWriter],
    alerter: FromDishka[BotAlert],
):
    try:
        game = await dao.game.get_full(game_id)
        assert author_id == game.author.id
        await start_game(
            game=game,
            dao=dao.game_starter,
            game_log=game_log_writer,
            view=game_view,
            scheduler=scheduler,
        )
    except Exception as e:
        await alerter.alert(f"game not started because of {e!s}")
        raise


@inject
async def send_hint_wrapper(
    level_id: int,
    team_id: int,
    hint_number: int,
    lt_id: int,
    dao: FromDishka[HolderDao],
    game_view: FromDishka[GameView],
    scheduler: FromDishka[Scheduler],
    alerter: FromDishka[BotAlert],
    current_game: FromDishka[CurrentGameProvider],
):
    try:
        level = await dao.level.get_by_id(level_id)
        team = await dao.team.get_by_id(team_id)
        game = await current_game.get_required_game()

        await send_hint(
            level=level,
            hint_number=hint_number,
            lt_id=lt_id,
            team=team,
            game=game,
            dao=dao.level_time,
            view=game_view,
            scheduler=scheduler,
        )
    except Exception as e:
        await alerter.alert(f"hint for team {team_id} not sent because of {e!s}")
        raise


@inject
async def send_hint_for_testing_wrapper(
    level_id: int,
    game_id: int,
    player_id: int,
    hint_number: int,
    dao: FromDishka[HolderDao],
    level_view: FromDishka[LevelView],
    scheduler: FromDishka[LevelTestScheduler],
):
    level = await dao.level.get_by_id(level_id)
    game = await dao.game.get_by_id(game_id)
    player = await dao.player.get_by_id(player_id)
    org = await get_by_player(dao=dao.organizer, game=game, player=player)

    await send_testing_level_hint(
        suite=dto.LevelTestSuite(level=level, tester=org),
        hint_number=hint_number,
        view=level_view,
        scheduler=scheduler,
        dao=dao.level_testing_complex,
    )


@inject
async def event_wrapper(
    team_id: int,
    started_level_time_id: int,
    dumped_effects: str,
    retort: FromDishka[Retort],
    interactor: FromDishka[GamePlayTimerInteractor],
):
    effects = retort.load(dumped_effects, action.Effects)
    await interactor(
        team_id=team_id,
        started_level_time_id=started_level_time_id,
        effects=effects,
        now=datetime.now(tz=tz_utc),
        input_container=SchedulerContainer(),
    )
