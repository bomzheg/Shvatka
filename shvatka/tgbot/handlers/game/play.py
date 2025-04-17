from aiogram import Router
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.models import dto
from shvatka.core.services.game_play import CheckKeyInteractor
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.filters import is_key, IsTeamFilter
from shvatka.tgbot.filters.game_status import GameStatusFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.middlewares import TeamPlayerMiddleware
from shvatka.tgbot.views.game import BotInputContainer


@inject
async def check_key_handler(
    message: Message,
    key: str,
    team: dto.Team,
    player: dto.Player,
    game: dto.Game,
    interactor: FromDishka[CheckKeyInteractor],
    dao: FromDishka[HolderDao],
):
    full_game = await dao.game.get_full(game.id)
    await interactor(
        key=key,
        input_container=BotInputContainer(message=message),
        player=player,
        team=team,
        game=full_game,
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
