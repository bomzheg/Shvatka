from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.dal.level_testing import LevelTestingDao
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.scheduler import LevelTestScheduler
from shvatka.core.models import dto
from shvatka.core.services.level import get_level_by_id_for_org
from shvatka.core.services.level_testing import start_level_test
from shvatka.core.services.organizers import get_org_by_id
from shvatka.core.utils.exceptions import PermissionsError
from shvatka.core.views.level import LevelView
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot import states
from shvatka.tgbot.utils.router import disable_router_on_game


@inject
async def start_test_level(
    c: CallbackQuery,
    callback_data: kb.LevelTestInviteCD,
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    scheduler: FromDishka[LevelTestScheduler],
    level_view: FromDishka[LevelView],
    level_testing: FromDishka[LevelTestingDao],
):
    player = await identity.get_required_player()
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
    await dialog_manager.start(
        states.LevelTestSG.wait_key,
        data={"level_id": callback_data.level_id, "org_id": org.id},
    )
    await start_level_test(suite=suite, scheduler=scheduler, view=level_view, dao=level_testing)


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)

    router.callback_query.register(start_test_level, kb.LevelTestInviteCD.filter())
    return router
