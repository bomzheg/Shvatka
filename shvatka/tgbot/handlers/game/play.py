from aiogram import Router
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

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


@inject
async def check_key_handler(
    _: Message,
    key: str,
    team: dto.Team,
    player: dto.Player,
    game: dto.Game,
    dao: FromDishka[HolderDao],
    scheduler: FromDishka[Scheduler],
    locker: FromDishka[KeyCheckerFactory],
    game_view: FromDishka[GameView],
    org_notifier: FromDishka[OrgNotifier],
    game_log: FromDishka[GameLogWriter],
):
    full_game = await dao.game.get_full(game.id)
    key_processor = KeyProcessor(dao=dao.game_player, game=full_game, locker=locker)
    await check_key(
        key=key,
        player=player,
        team=team,
        game=full_game,
        dao=dao.game_player,
        view=game_view,
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
