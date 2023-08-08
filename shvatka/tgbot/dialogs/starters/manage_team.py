from aiogram import Router
from aiogram.filters import Command, or_f

from shvatka.tgbot import states
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.middlewares import TeamPlayerMiddleware
from shvatka.tgbot.utils.router import register_start_handler
from shvatka.tgbot.views.commands import MANAGE_TEAM_COMMAND


def setup() -> Router:
    router = Router(name=__name__)
    router.message.outer_middleware.register(TeamPlayerMiddleware())
    router.callback_query.outer_middleware.register(TeamPlayerMiddleware())

    register_start_handler(
        Command(commands=MANAGE_TEAM_COMMAND),
        or_f(
            TeamPlayerFilter(is_captain=True),
            TeamPlayerFilter(can_manage_players=True),
            TeamPlayerFilter(can_remove_players=True),
            TeamPlayerFilter(can_change_team_name=True),
        ),
        state=states.CaptainsBridgeSG.main,
        router=router,
    )
    return router
