from functools import partial

from aiogram import Router, types
from aiogram.filters import Command, CommandObject

from shvatka.core.services.team import get_team_by_id, merge_teams
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.filters import is_superuser
from shvatka.tgbot.views.commands import MERGE_TEAMS


async def merge_teams_command(
        message: types.Message,
        command: CommandObject,
        game_log: GameLogWriter,
        dao: HolderDao,
):
    old_id, new_id = map(int, command.args.split())
    primary = await get_team_by_id(new_id, dao.team)
    assert primary.captain
    secondary = await get_team_by_id(old_id, dao.team)
    await merge_teams(primary.captain, primary, secondary, game_log, dao.team_merger)
    await message.reply(f"Успешно объединены {primary.name} и {secondary.name}")


def setup(bot_config: BotConfig) -> Router:
    router = Router(name=__name__)
    is_superuser_ = partial(is_superuser, superusers=bot_config.superusers)
    router.message.filter(is_superuser_)

    router.message.register(merge_teams, Command(MERGE_TEAMS))

    return router
