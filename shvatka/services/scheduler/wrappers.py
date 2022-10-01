from contextlib import asynccontextmanager
from typing import AsyncContextManager

from db.dao.holder import HolderDao
from shvatka.models.dto.scheduled_context import ScheduledContext
from shvatka.services.game_play import prepare_game, start_game
from shvatka.services.scheduler.context import ScheduledContextHolder


@asynccontextmanager
async def prepare_context() -> AsyncContextManager[ScheduledContext]:
    async with ScheduledContextHolder.poll() as session:
        dao = HolderDao(session=session, redis=ScheduledContextHolder.redis)
        yield ScheduledContext(dao=dao, bot=ScheduledContextHolder.bot)


async def prepare_game_wrapper(game_id: int, author_id: int):
    async with prepare_context as context:
        author = await context.dao.player.get_by_id(author_id)
        game = await context.dao.game.get_by_id(game_id, author)
        await prepare_game(game, context)


async def start_game_wrapper(game_id: int, author_id: int):
    async with prepare_context as context:
        author = await context.dao.player.get_by_id(author_id)
        game = await context.dao.game.get_by_id(game_id, author)
        await start_game(game, context)
