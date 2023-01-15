import typing

from aiogram import Bot, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager

from infrastructure.db.dao.holder import HolderDao
from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.interfaces.scheduler import Scheduler
from shvatka.models import dto
from shvatka.services.game_play import check_key
from shvatka.utils.exceptions import InvalidKey
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from tgbot import states
from tgbot.config.models.bot import BotConfig
from tgbot.filters import is_key, IsTeamFilter
from tgbot.filters.game_status import GameStatusFilter
from tgbot.filters.team_player import TeamPlayerFilter
from tgbot.views.commands import SPY_COMMAND, SPY_LEVELS_COMMAND, SPY_KEYS_COMMAND
from tgbot.views.game import GameBotLog, create_bot_game_view, BotOrgNotifier


async def check_key_handler(
    m: Message,
    team: dto.Team,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
    scheduler: Scheduler,
    locker: KeyCheckerFactory,
    bot: Bot,
    config: BotConfig,
    file_storage: FileStorage,
):
    try:
        await check_key(
            key=typing.cast(str, m.text),
            player=player,
            team=team,
            game=await dao.game.get_full(game.id),
            dao=dao.game_player,
            view=create_bot_game_view(bot=bot, dao=dao, storage=file_storage),
            game_log=GameBotLog(bot=bot, log_chat_id=config.log_chat),
            org_notifier=BotOrgNotifier(bot=bot),
            locker=locker,
            scheduler=scheduler,
        )
    except InvalidKey:
        raise SkipHandler


async def spy_menu(_: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.OrgSpySG.main)


async def spy_levels(_: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.OrgSpySG.spy)


async def spy_keys(_: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.OrgSpySG.keys)


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(GameStatusFilter(running=True))
    router.message.register(
        check_key_handler,
        is_key,
        IsTeamFilter(),
        TeamPlayerFilter(),
    )  # TODO is playing in this game
    router.message.register(spy_menu, Command(commands=SPY_COMMAND))  # is_org
    router.message.register(spy_levels, Command(commands=SPY_LEVELS_COMMAND))  # is_org
    router.message.register(spy_keys, Command(commands=SPY_KEYS_COMMAND))  # is_org
    return router
