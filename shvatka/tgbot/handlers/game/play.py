from aiogram import Router
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.games.interactors import CheckKeyInteractor
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.tgbot.filters import IsTeamFilter, SentAfterGameStartFilter, is_key
from shvatka.tgbot.filters.game_status import GameStatusFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
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
    router.message.filter(GameStatusFilter(running=True))
    router.edited_message.filter(GameStatusFilter(running=True))
    router.message.register(
        check_key_handler,
        is_key,
        IsTeamFilter(),
        TeamPlayerFilter(),
    )  # TODO is playing in this game
    # a typo is usually fixed by editing the message rather than sending it again,
    # so an edit counts as typing the key — but only of a message written after
    # the game started, never of something the chat has been carrying since before
    router.edited_message.register(
        check_key_handler,
        is_key,
        SentAfterGameStartFilter(),
        IsTeamFilter(),
        TeamPlayerFilter(),
    )
    return router
