from aiogram import Router
from aiogram.filters import CommandObject, Command
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.nursery import Nursery
from shvatka.core.services.game import get_full_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.tasks import PublishScenarioToForumParams, PublishScenarioToForumTask
from shvatka.tgbot.utils.router import disable_router_on_game
from shvatka.tgbot.views.commands import PUBLISH_COMMAND


@inject
async def publish_game_forum(
    m: Message,
    command: CommandObject,
    dao: HolderDao,
    identity: FromDishka[IdentityProvider],
    nursery: FromDishka[Nursery],
):
    if not command.args:
        return
    game_id, username, password = map(str.strip, command.args.split(maxsplit=2))
    player = await identity.get_required_player()
    # authorize here so a player without rights is told right away, not in a
    # background task nobody is looking at; the task checks again on its own
    await get_full_game(id_=int(game_id), identity=identity, dao=dao.game)
    nursery.spawn(
        PublishScenarioToForumTask,
        PublishScenarioToForumParams(
            game_id=int(game_id),
            player_id=player.id,
            username=username,
            password=password,
            chat_id=m.chat.id,
        ),
    )


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)

    router.message.register(publish_game_forum, Command(PUBLISH_COMMAND))
    return router
