from functools import partial

from aiogram import Router, Bot
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.api.protocols import BgManagerFactory

from shvatka.core.services.player import get_player_by_id, merge_players
from shvatka.core.services.team import get_team_by_id, merge_teams
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.filters import is_superuser
from shvatka.tgbot.utils.router import disable_router_on_game


async def confirm_merge_not_superuser(callback_query: CallbackQuery):
    await callback_query.answer("Недостаточно прав, сорян", cache_time=3600)


async def confirm_merge_team(
    callback_query: CallbackQuery,
    callback_data: kb.TeamMergeCD,
    dao: HolderDao,
    game_log: GameLogWriter,
    bg_manager_factory: BgManagerFactory,
    bot: Bot,
):
    primary = await get_team_by_id(callback_data.primary_team_id, dao.team)
    assert primary.captain
    secondary = await get_team_by_id(callback_data.secondary_team_id, dao.team)
    await merge_teams(primary.captain, primary, secondary, game_log, dao.team_merger)
    await callback_query.answer("Успешно объединено")
    assert isinstance(callback_query.message, Message)
    await callback_query.message.edit_reply_markup(reply_markup=None)
    captain_chat_id = primary.captain.get_chat_id()
    bg = bg_manager_factory.bg(bot=bot, user_id=captain_chat_id, chat_id=captain_chat_id)
    await bg.update({})


async def confirm_merge_players(
    callback_query: CallbackQuery,
    callback_data: kb.PlayerMergeCD,
    dao: HolderDao,
    game_log: GameLogWriter,
    bg_manager_factory: BgManagerFactory,
    bot: Bot,
):
    primary = await get_player_by_id(callback_data.primary_player_id, dao.player)
    secondary = await get_player_by_id(callback_data.secondary_player_id, dao.player)
    await merge_players(primary, secondary, game_log, dao.player_merger)
    await callback_query.answer("Успешно объединено")
    assert isinstance(callback_query.message, Message)
    await callback_query.message.edit_reply_markup(reply_markup=None)
    primary_chat_id = primary.get_chat_id()
    bg = bg_manager_factory.bg(bot=bot, user_id=primary_chat_id, chat_id=primary_chat_id)
    await bg.update({})


def setup(bot_config: BotConfig) -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)
    is_superuser_ = partial(is_superuser, superusers=bot_config.superusers)
    router.callback_query.register(confirm_merge_team, kb.TeamMergeCD.filter(), is_superuser_)
    router.callback_query.register(confirm_merge_not_superuser, kb.TeamMergeCD.filter())
    router.callback_query.register(confirm_merge_players, kb.PlayerMergeCD.filter(), is_superuser_)
    router.callback_query.register(confirm_merge_not_superuser, kb.PlayerMergeCD.filter())
    return router
