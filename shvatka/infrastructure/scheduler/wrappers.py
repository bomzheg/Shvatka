from aiogram import Bot
from dishka.integrations.base import FromDishka

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.scheduler.context import inject
from shvatka.core.interfaces.scheduler import LevelTestScheduler, Scheduler
from shvatka.core.models import dto
from shvatka.core.services.game_play import prepare_game, start_game, send_hint
from shvatka.core.services.level_testing import send_testing_level_hint
from shvatka.core.services.organizers import get_by_player
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.game import GameBotLog, create_bot_game_view
from shvatka.tgbot.views.level_testing import create_level_test_view


@inject
async def prepare_game_wrapper(
    game_id: int,
    author_id: int,
    dao: FromDishka[HolderDao],
    bot: FromDishka[Bot],
    file_storage: FromDishka[FileStorage],
) -> None:
    author = await dao.player.get_by_id(author_id)
    game = await dao.game.get_by_id(game_id, author)
    await prepare_game(
        game=game,
        game_preparer=dao.game_preparer,
        view_preparer=create_bot_game_view(bot, dao, file_storage),
    )


@inject
async def start_game_wrapper(
    game_id: int,
    author_id: int,
    dao: FromDishka[HolderDao],
    bot: FromDishka[Bot],
    file_storage: FromDishka[FileStorage],
    scheduler: FromDishka[Scheduler],
    config: FromDishka[BotConfig],
):
    game = await dao.game.get_full(game_id)
    assert author_id == game.author.id
    await start_game(
        game=game,
        dao=dao.game_starter,
        game_log=GameBotLog(bot=bot, log_chat_id=config.game_log_chat),
        view=create_bot_game_view(bot, dao, file_storage),
        scheduler=scheduler,
    )


@inject
async def send_hint_wrapper(
    level_id: int,
    team_id: int,
    hint_number: int,
    dao: FromDishka[HolderDao],
    bot: FromDishka[Bot],
    file_storage: FromDishka[FileStorage],
    scheduler: FromDishka[Scheduler],
):
    level = await dao.level.get_by_id(level_id)
    team = await dao.team.get_by_id(team_id)

    await send_hint(
        level=level,
        hint_number=hint_number,
        team=team,
        dao=dao.level_time,
        view=create_bot_game_view(bot, dao, file_storage),
        scheduler=scheduler,
    )


@inject
async def send_hint_for_testing_wrapper(
    level_id: int,
    game_id: int,
    player_id: int,
    hint_number: int,
    dao: FromDishka[HolderDao],
    bot: FromDishka[Bot],
    file_storage: FromDishka[FileStorage],
    scheduler: FromDishka[LevelTestScheduler],
):
    level = await dao.level.get_by_id(level_id)
    game = await dao.game.get_by_id(game_id)
    player = await dao.player.get_by_id(player_id)
    org = await get_by_player(dao=dao.organizer, game=game, player=player)

    await send_testing_level_hint(
        suite=dto.LevelTestSuite(level=level, tester=org),
        hint_number=hint_number,
        view=create_level_test_view(bot, dao, file_storage),
        scheduler=scheduler,
        dao=dao.level_testing_complex,
    )
