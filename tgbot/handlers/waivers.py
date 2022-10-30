from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums import GameStatus
from shvatka.services.waiver import add_vote
from shvatka.utils.exceptions import PlayerNotInTeam
from tgbot import keyboards as kb
from tgbot.filters.game_status import GameStatusFilter
from tgbot.services.waiver import swap_saved_message
from tgbot.views.commands import START_WAIVERS_COMMAND
from tgbot.views.utils import total_remove_msg
from tgbot.views.waiver import get_waiver_poll_text


async def start_waivers(m: Message, team: dto.Team, game: dto.Game, dao: HolderDao, bot: Bot):
    msg = await m.answer(
        text=await get_waiver_poll_text(team, game, dao),
        reply_markup=kb.get_kb_waivers(team),
        disable_web_page_preview=True,
    )
    old_msg_id = await swap_saved_message(game, msg, dao.poll)
    await total_remove_msg(bot, m.chat.id, old_msg_id)


async def add_vote_handler(
    c: CallbackQuery,
    callback_data: kb.WaiverCD,
    player: dto.Player,
    team: dto.Team,
    game: dto.Game,
    dao: HolderDao,
):
    if team.id != callback_data.team_id:
        raise PlayerNotInTeam(player=player, team=team)
    await add_vote(
        game=game, team=team, player=player, vote=callback_data.vote, dao=dao.waiver_vote_adder,
    )
    await c.answer()
    await c.message.edit_text(
        text=await get_waiver_poll_text(team, game, dao),
        reply_markup=kb.get_kb_waivers(team),
        disable_web_page_preview=True,
    )


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(
        GameStatusFilter(status=GameStatus.getting_waivers),
    )
    router.callback_query.filter(
        GameStatusFilter(status=GameStatus.getting_waivers),
    )
    # is_team=True, can_manage_waivers=True
    router.message.register(start_waivers, Command(START_WAIVERS_COMMAND))
    # is_team_player
    router.callback_query.register(add_vote_handler, kb.WaiverCD.filter())
    return router
