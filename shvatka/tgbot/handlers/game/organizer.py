import asyncio

from aiogram import Router, Bot
from aiogram.filters import CommandObject, Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import LevelTestScheduler
from shvatka.core.models import dto
from shvatka.core.services.game import get_full_game
from shvatka.core.services.level import get_level_by_id_for_org
from shvatka.core.services.level_testing import start_level_test
from shvatka.core.services.organizers import get_org_by_id
from shvatka.core.utils.exceptions import PermissionsError
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot import states
from shvatka.tgbot.dialogs.game_manage.handlers import upload_wrapper
from shvatka.tgbot.utils.router import disable_router_on_game
from shvatka.tgbot.views.commands import PUBLISH_COMMAND
from shvatka.tgbot.views.level_testing import create_level_test_view


async def start_test_level(
    c: CallbackQuery,
    player: dto.Player,
    callback_data: kb.LevelTestInviteCD,
    dao: HolderDao,
    dialog_manager: DialogManager,
    scheduler: LevelTestScheduler,
    bot: Bot,
    file_storage: FileStorage,
):
    await c.answer()
    org = await get_org_by_id(callback_data.org_id, dao.organizer)
    if org.player.id != player.id:
        raise PermissionsError(
            notify_user="Игрок пытается начать тестирование уровня "
            "предназначенное для другого игрока",
            player=player,
            game=org.game,
            alarm=True,
        )
    level = await get_level_by_id_for_org(callback_data.level_id, org, dao.level)
    suite = dto.LevelTestSuite(tester=org, level=level)
    view = create_level_test_view(bot=bot, dao=dao, storage=file_storage)
    await dialog_manager.start(
        states.LevelTestSG.wait_key,
        data={"level_id": callback_data.level_id, "org_id": org.id},
    )
    await start_level_test(
        suite=suite, scheduler=scheduler, view=view, dao=dao.level_testing_complex
    )


async def publish_game_forum(
    m: Message, command: CommandObject, player: dto.Player, dao: HolderDao
):
    if not command.args:
        return
    game_id, username, password = map(str.strip, command.args.split(maxsplit=2))
    game_ = await get_full_game(int(game_id), player, dao.game)
    asyncio.create_task(upload_wrapper(game_, username, password, m))


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)

    router.callback_query.register(start_test_level, kb.LevelTestInviteCD.filter())
    router.message.register(publish_game_forum, Command(PUBLISH_COMMAND))
    return router
