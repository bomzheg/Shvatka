from contextlib import asynccontextmanager
from typing import AsyncContextManager

from db.dao.holder import HolderDao
from scheduler.context import ScheduledContextHolder, ScheduledContext
from shvatka.services.game_play import prepare_game, start_game, send_hint
from tgbot.views.game import GameBotLog, BotView
from tgbot.views.hint_content_resolver import HintContentResolver
from tgbot.views.hint_sender import HintSender


@asynccontextmanager
async def prepare_context() -> AsyncContextManager[ScheduledContext]:
    async with ScheduledContextHolder.poll() as session:
        dao = HolderDao(session=session, redis=ScheduledContextHolder.redis)
        yield ScheduledContext(
            dao=dao,
            bot=ScheduledContextHolder.bot,
            scheduler=ScheduledContextHolder.scheduler,
            game_log_chat=ScheduledContextHolder.game_log_chat,
        )


async def prepare_game_wrapper(game_id: int, author_id: int):
    async with prepare_context as context:  # TODO AttributeError: __aenter__
        author = await context.dao.player.get_by_id(author_id)
        game = await context.dao.game.get_by_id(game_id, author)
        await prepare_game(game, context.dao.game_preparer, _create_game_view(context))


async def start_game_wrapper(game_id: int, author_id: int):
    async with prepare_context as context:
        context: ScheduledContext
        game = await context.dao.game.get_full(game_id)
        assert author_id == game.author.id
        await start_game(
            game=game,
            dao=context.dao.game_starter,
            game_log=GameBotLog(bot=context.bot, log_chat_id=context.game_log_chat),
            view=_create_game_view(context),
            scheduler=context.scheduler,
        )


async def send_hint_wrapper(level_id: int, team_id: int, hint_number: int):
    async with prepare_context as context:
        context: ScheduledContext
        level = await context.dao.level.get_by_id(level_id)
        team = await context.dao.team.get_by_id(team_id)

        await send_hint(
            level=level,
            hint_number=hint_number,
            team=team,
            dao=context.dao.level_time,
            view=_create_game_view(context),
            scheduler=context.scheduler,
        )


def _create_game_view(context: ScheduledContext) -> BotView:
    return BotView(
        bot=context.bot,
        hint_sender=HintSender(
            bot=context.bot,
            resolver=HintContentResolver(dao=context.dao.file_info),
        ),
    )
