import typing
from contextlib import asynccontextmanager
from typing import AsyncIterator

from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.scheduler.context import ScheduledContextHolder, ScheduledContext
from shvatka.core.interfaces.scheduler import LevelTestScheduler
from shvatka.core.models import dto
from shvatka.core.services.game_play import prepare_game, start_game, send_hint
from shvatka.core.services.level_testing import send_testing_level_hint
from shvatka.core.services.organizers import get_by_player
from shvatka.tgbot.views.game import GameBotLog, create_bot_game_view
from shvatka.tgbot.views.level_testing import create_level_test_view


@asynccontextmanager
async def prepare_context() -> AsyncIterator[ScheduledContext]:
    async with ScheduledContextHolder.pool() as session:
        dao = HolderDao(
            session=session,
            redis=ScheduledContextHolder.redis,
            level_test=ScheduledContextHolder.level_test_dao,
        )
        yield ScheduledContext(
            dao=dao,
            bot=ScheduledContextHolder.bot,
            scheduler=ScheduledContextHolder.scheduler,
            game_log_chat=ScheduledContextHolder.game_log_chat,
            file_storage=ScheduledContextHolder.file_storage,
        )


async def prepare_game_wrapper(game_id: int, author_id: int):
    async with prepare_context() as context:  # type: ScheduledContext
        author = await context.dao.player.get_by_id(author_id)
        game = await context.dao.game.get_by_id(game_id, author)
        await prepare_game(
            game=game,
            game_preparer=context.dao.game_preparer,
            view_preparer=create_bot_game_view(context.bot, context.dao, context.file_storage),
        )


async def start_game_wrapper(game_id: int, author_id: int):
    async with prepare_context() as context:  # type: ScheduledContext
        game = await context.dao.game.get_full(game_id)
        assert author_id == game.author.id
        await start_game(
            game=game,
            dao=context.dao.game_starter,
            game_log=GameBotLog(bot=context.bot, log_chat_id=context.game_log_chat),
            view=create_bot_game_view(context.bot, context.dao, context.file_storage),
            scheduler=context.scheduler,
        )


async def send_hint_wrapper(level_id: int, team_id: int, hint_number: int):
    async with prepare_context() as context:  # type: ScheduledContext
        level = await context.dao.level.get_by_id(level_id)
        team = await context.dao.team.get_by_id(team_id)

        await send_hint(
            level=level,
            hint_number=hint_number,
            team=team,
            dao=context.dao.level_time,
            view=create_bot_game_view(context.bot, context.dao, context.file_storage),
            scheduler=context.scheduler,
        )


async def send_hint_for_testing_wrapper(
    level_id: int, game_id: int, player_id: int, hint_number: int
):
    async with prepare_context() as context:  # type: ScheduledContext
        level = await context.dao.level.get_by_id(level_id)
        game = await context.dao.game.get_by_id(game_id)
        player = await context.dao.player.get_by_id(player_id)
        org = await get_by_player(dao=context.dao.organizer, game=game, player=player)

        await send_testing_level_hint(
            suite=dto.LevelTestSuite(level=level, tester=org),
            hint_number=hint_number,
            view=create_level_test_view(context.bot, context.dao, context.file_storage),
            scheduler=typing.cast(
                LevelTestScheduler, context.scheduler
            ),  # TODO typing.cast replace with better hint
            dao=context.dao.level_testing_complex,
        )
