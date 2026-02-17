from aiogram import Router
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.games.interactors import CheckKeyInteractor
from shvatka.tgbot.filters import is_key, IsTeamFilter
from shvatka.tgbot.filters.game_status import GameStatusFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.middlewares import TeamPlayerMiddleware
from shvatka.tgbot.views.game import BotInputContainer


@inject
async def check_key_handler(
    message: Message,
    key: str,
    interactor: FromDishka[CheckKeyInteractor],
    identity: FromDishka[IdentityProvider],
):
    await interactor(
        key=key,
        input_container=BotInputContainer(message=message),
        identity=identity,
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
