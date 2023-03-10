import typing

from aiogram import Bot, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.services.game_play import check_key
from shvatka.core.utils.exceptions import InvalidKey
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.filters import is_key, IsTeamFilter
from shvatka.tgbot.filters.game_status import GameStatusFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.utils.router import register_start_handler
from shvatka.tgbot.views.commands import SPY_COMMAND, SPY_LEVELS_COMMAND, SPY_KEYS_COMMAND
from shvatka.tgbot.views.game import GameBotLog, create_bot_game_view, BotOrgNotifier


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


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(GameStatusFilter(running=True))
    router.message.register(
        check_key_handler,
        is_key,
        IsTeamFilter(),
        TeamPlayerFilter(),
    )  # TODO is playing in this game
    register_start_handler(
        Command(commands=SPY_COMMAND), state=states.OrgSpySG.main, router=router  # TODO is_org
    )
    register_start_handler(
        Command(commands=SPY_LEVELS_COMMAND),  # TODO is_org
        state=states.OrgSpySG.spy,
        router=router,
    )
    register_start_handler(
        Command(commands=SPY_KEYS_COMMAND),  # TODO is_org
        state=states.OrgSpySG.keys,
        router=router,
    )
    return router
