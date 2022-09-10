from contextlib import asynccontextmanager
from typing import AsyncContextManager

from app.dao.holder import HolderDao
from app.models import dto
from app.services.game_play import prepare_game, start_game
from app.services.scheduler.context import ScheduledContextHolder


@asynccontextmanager
async def prepare_context() -> AsyncContextManager[dto.ScheduledContext]:
    async with ScheduledContextHolder.poll() as session:
        dao = HolderDao(session=session, redis=ScheduledContextHolder.redis)
        yield dto.ScheduledContext(dao=dao, bot=ScheduledContextHolder.bot)


async def prepare_game_wrapper(game: dto.Game):
    async with prepare_context as context:
        await prepare_game(game, context)


async def start_game_wrapper(game: dto.Game):
    async with prepare_context as context:
        await start_game(game, context)
