from aiogram import Bot, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.scheduler import Scheduler
from shvatka.services.game_play import check_key
from shvatka.utils.exceptions import InvalidKey
from shvatka.utils.key_checker_lock import KeyCheckerFactory
from tgbot.config.models.bot import BotConfig
from tgbot.filters import is_key
from tgbot.filters.game_status import GameStatusFilter
from tgbot.states import OrgSpy
from tgbot.views.commands import SPY_COMMAND
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
            key=m.text,
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


async def spy_menu(m: Message, dialog_manager: DialogManager):
    await dialog_manager.start(OrgSpy.main)


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(GameStatusFilter(running=True))
    router.message.register(
        check_key_handler, is_key,
    )  # is_team, is_played_player is_key
    router.message.register(spy_menu, Command(commands=SPY_COMMAND))  # is_org
    return router
