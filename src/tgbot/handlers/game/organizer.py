from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from src.infrastructure.db.dao.holder import HolderDao
from src.core.interfaces.clients.file_storage import FileStorage
from src.core.interfaces.scheduler import LevelTestScheduler
from src.core.models import dto
from src.core.services.level import get_level_by_id_for_org
from src.core.services.level_testing import start_level_test
from src.core.services.organizers import get_org_by_id
from src.core.utils.exceptions import PermissionsError
from src.tgbot import keyboards as kb
from src.tgbot import states
from src.tgbot.utils.router import disable_router_on_game
from src.tgbot.views.level_testing import create_level_test_view


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
            notify_user=f"Игрок пытается начать тестирование уровня предназначенное для другого игрока",
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


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)

    router.callback_query.register(start_test_level, kb.LevelTestInviteCD.filter())
    return router
