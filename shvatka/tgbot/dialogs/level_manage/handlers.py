import logging
import typing
from typing import Any

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import AsyncContainer, FromDishka
from dishka.integrations.aiogram import CONTAINER_NAME
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.dal.level import LevelDeleter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.nursery import Nursery
from shvatka.core.interfaces.scheduler import LevelTestScheduler
from shvatka.core.models import dto
from shvatka.core.services.level import get_by_id, unlink_level, delete_level
from shvatka.core.services.level_testing import start_level_test, check_level_testing_key
from shvatka.core.services.organizers import get_org_by_id
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import OrgNotifier
from shvatka.core.views.level import LevelView
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot.tasks import send_level_hints
from shvatka.tgbot.views.user import render_small_card_link
from .getters import get_level_and_org, get_org

logger = logging.getLogger(__name__)


async def edit_level(c: CallbackQuery, button: Button, manager: DialogManager):
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    await manager.start(state=states.LevelEditSg.menu, data={"level_id": data["level_id"]})


@inject
async def show_level(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    dao: FromDishka[HolderDao],
    identity: FromDishka[IdentityProvider],
    nursery: FromDishka[Nursery],
):
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    level_id = data["level_id"]
    author = await identity.get_required_player()
    level = await get_by_id(level_id, author, dao.level)
    chat_id = author.get_chat_id()
    if chat_id is None:
        logger.warning("player %s has no telegram chat, hints not sent", author.id)
        return
    nursery.spawn(send_level_hints, level=level, chat_id=chat_id)


@inject
async def send_to_testing(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    org_id: str,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
):
    bot: Bot = manager.middleware_data["bot"]
    author = await identity.get_required_player()
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    level = await get_by_id(data["level_id"], author, dao.level)
    org = await get_org_by_id(id_=int(org_id), dao=dao.organizer)
    await bot.send_message(
        chat_id=org.player.get_chat_id(),  # type: ignore[arg-type]
        text=f"{render_small_card_link(author)} "
        f"предлагает протестировать уровень {level.name_id}. "
        f"Начать прямо сейчас?",
        reply_markup=kb.get_kb_level_test_invite(level, org),
    )
    await c.answer("Приглашение отправлено")


@inject
async def level_testing(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    scheduler: FromDishka[LevelTestScheduler],
    view: FromDishka[LevelView],
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
) -> None:
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    level_id = data["level_id"]
    author = await identity.get_required_player()
    level = await get_by_id(level_id, author, dao.level)
    org = await get_org(author, level, dao)
    if org is None:
        logger.warning("org is none?!")
        await manager.done()
        return
    suite = dto.LevelTestSuite(tester=org, level=level)
    await manager.start(state=states.LevelTestSG.wait_key, data={"level_id": level_id})
    await start_level_test(
        suite=suite, scheduler=scheduler, view=view, dao=dao.level_testing_complex
    )


@inject
async def unlink_level_handler(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
):
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    level_id = data["level_id"]
    author = await identity.get_required_player()
    level = await get_by_id(level_id, author, dao.level)
    await unlink_level(level, author, dao.level)
    await manager.done()


@inject
async def delete_level_handler(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    dao: FromDishka[HolderDao],
    level_deleter: FromDishka[LevelDeleter],
    identity: FromDishka[IdentityProvider],
) -> None:
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    level_id = data["level_id"]
    author = await identity.get_required_player()
    level = await get_by_id(level_id, author, dao.level)
    await delete_level(level, author, level_deleter)
    await manager.done()


@inject
async def cancel_level_test(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
):
    author = await identity.get_required_player()
    level, org = await get_level_and_org(author, dao, manager)
    if org is None:
        logger.warning("org is none?!")
        await manager.done()
        return
    suite = dto.LevelTestSuite(tester=org, level=level)
    await dao.level_test.cancel_test(suite=suite)
    await manager.done()


@inject
async def process_key_message(
    m: Message, dialog_: Any, manager: DialogManager, identity: FromDishka[IdentityProvider]
) -> None:
    dishka: AsyncContainer = manager.middleware_data[CONTAINER_NAME]
    author = await identity.get_required_player()
    dao = await dishka.get(HolderDao)
    locker = await dishka.get(KeyCheckerFactory)
    level, org = await get_level_and_org(author, dao, manager)
    if org is None:
        logger.warning("org is none?!")
        await manager.done()
        return
    suite = dto.LevelTestSuite(tester=org, level=level)
    view = await dishka.get(LevelView)
    org_notifier = await dishka.get(OrgNotifier)
    insert_result = await check_level_testing_key(
        key=typing.cast(str, m.text),
        suite=suite,
        view=view,
        org_notifier=org_notifier,
        locker=locker,
        dao=dao.level_testing_complex,
    )
    if insert_result.level_completed:
        await manager.done()


async def select_level_handler(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: int
):
    await manager.start(state=states.LevelManageSG.menu, data={"level_id": int(item_id)})
