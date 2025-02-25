from functools import partial

from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject

from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.core.models import dto
from shvatka.tgbot import keyboards as kb
from shvatka.core.services.team import get_team_by_id, merge_teams
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.filters import is_superuser
from shvatka.tgbot.views.commands import MERGE_TEAMS, MERGE_PLAYERS


async def merge_teams_command(
    message: types.Message,
    command: CommandObject,
    game_log: GameLogWriter,
    dao: HolderDao,
):
    if not command.args:
        await message.reply(
            "После команды следует указать аргументы. "
            "Сначала id команды в новом движке, а потом id команды с форума."
        )
        return
    old_id, new_id = map(int, command.args.split())
    primary = await get_team_by_id(new_id, dao.team)
    assert primary.captain
    secondary = await get_team_by_id(old_id, dao.team)
    await merge_teams(primary.captain, primary, secondary, game_log, dao.team_merger)
    await message.reply(f"Успешно объединены {primary.name} и {secondary.name}")


async def merge_players_command(
    message: types.Message,
    bot: Bot,
    player: dto.Player,
    config: BotConfig,
    command: CommandObject,
    dao: HolderDao,
):
    if not command.args:
        await message.reply(
            "После команды следует указать аргументы. "
            "Сначала id игрока в новом движке, а потом id игрока с форума."
        )
        return
    old_id, new_id = map(int, command.args.split())
    primary = await dao.player.get_by_id(new_id)
    secondary = await dao.player.get_by_id(old_id)
    await bot.send_message(
        chat_id=config.game_log_chat,
        text=f"Админ {hd.quote(player.name_mention)} предлагает объединить "
        f"достижения игрока {hd.quote(primary.name_mention)}"
        f"с форумной версией {hd.quote(secondary.name_mention)}",
        reply_markup=kb.get_player_merge_confirm_kb(primary, secondary),
    )


def setup(bot_config: BotConfig) -> Router:
    router = Router(name=__name__)
    is_superuser_ = partial(is_superuser, superusers=bot_config.superusers)
    router.message.filter(is_superuser_)

    router.message.register(merge_teams, Command(MERGE_TEAMS))
    router.message.register(merge_players_command, Command(MERGE_PLAYERS))

    return router
