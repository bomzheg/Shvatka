from aiogram import Bot, Router
from aiogram.types import Message
from dishka import AsyncContainer

from shvatka.core.games.adapters import GamePlayKeyRepo
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.services.game_play import check_key
from shvatka.core.services.key import KeyProcessor
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import GameLogWriter, GameView, OrgNotifier
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.filters import is_key, IsTeamFilter
from shvatka.tgbot.filters.game_status import GameStatusFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.middlewares import TeamPlayerMiddleware


async def check_key_handler(
    _: Message,
    key: str,
    team: dto.Team,
    player: dto.Player,
    game: dto.Game,
    scheduler: Scheduler,
    locker: KeyCheckerFactory,
    game_log: GameLogWriter,
    dishka: AsyncContainer,
):
    repo_ = await dishka.get(GamePlayKeyRepo)
    key_processor = await dishka.get(KeyProcessor)
    view = await dishka.get(GameView)
    org_notifier = await dishka.get(OrgNotifier)
    await check_key(
        key=key,
        player=player,
        team=team,
        game=game,
        dao=repo_,
        view=view,
        game_log=game_log,
        org_notifier=org_notifier,
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
    return router
