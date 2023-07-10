from aiogram import Bot, Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.services.game_play import check_key
from shvatka.core.services.key import KeyProcessor
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.filters import is_key, IsTeamFilter
from shvatka.tgbot.filters.game_status import GameStatusFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.middlewares import TeamPlayerMiddleware
from shvatka.tgbot.utils.router import register_start_handler
from shvatka.tgbot.views.commands import SPY_COMMAND, SPY_LEVELS_COMMAND, SPY_KEYS_COMMAND
from shvatka.tgbot.views.game import create_bot_game_view, BotOrgNotifier


async def check_key_handler(
    _: Message,
    key: str,
    team: dto.Team,
    player: dto.Player,
    game: dto.Game,
    dao: HolderDao,
    scheduler: Scheduler,
    locker: KeyCheckerFactory,
    bot: Bot,
    file_storage: FileStorage,
    game_log: GameLogWriter,
):
    full_game = await dao.game.get_full(game.id)
    key_processor = KeyProcessor(dao=dao.game_player, game=full_game, locker=locker)
    await check_key(
        key=key,
        player=player,
        team=team,
        game=full_game,
        dao=dao.game_player,
        view=create_bot_game_view(bot=bot, dao=dao, storage=file_storage),
        game_log=game_log,
        org_notifier=BotOrgNotifier(bot=bot),
        locker=locker,
        scheduler=scheduler,
        key_processor=key_processor,
    )


def setup() -> Router:
    router = Router(name=__name__)
    router.message.outer_middleware(TeamPlayerMiddleware())
    router.message.filter(GameStatusFilter(running=True))
    router.message.register(
        check_key_handler,
        is_key,
        IsTeamFilter(),
        TeamPlayerFilter(),
    )  # TODO is playing in this game
    register_start_handler(
        F.chat.type == ChatType.PRIVATE,
        Command(commands=SPY_COMMAND),
        state=states.OrgSpySG.main,
        router=router,  # TODO is_org
    )
    register_start_handler(
        Command(commands=SPY_LEVELS_COMMAND),  # TODO is_org
        F.chat.type == ChatType.PRIVATE,
        state=states.OrgSpySG.spy,
        router=router,
    )
    register_start_handler(
        Command(commands=SPY_KEYS_COMMAND),  # TODO is_org
        F.chat.type == ChatType.PRIVATE,
        state=states.OrgSpySG.keys,
        router=router,
    )
    return router
