from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.infrastructure.db.dao.holder import HolderDao
from src.core.models import dto
from src.core.services.waiver import get_all_played
from src.tgbot.filters import GameStatusFilter
from src.tgbot.views.commands import GET_WAIVERS_COMMAND
from src.tgbot.views.waiver import render_all_teams_waivers


async def get_waivers_cmd(m: Message, game: dto.Game, dao: HolderDao):
    votes = await get_all_played(game=game, dao=dao.waiver)
    await m.answer(
        text=render_all_teams_waivers(votes),
        disable_web_page_preview=True,
    )


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(
        GameStatusFilter(active=True),
    )
    router.callback_query.filter(
        GameStatusFilter(active=True),
    )
    router.message.register(get_waivers_cmd, Command(GET_WAIVERS_COMMAND))
    return router
