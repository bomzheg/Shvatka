import asyncio
import typing
from typing import Any

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import LevelTestScheduler
from shvatka.core.models import dto
from shvatka.core.services.level import get_by_id, unlink_level
from shvatka.core.services.level_testing import start_level_test, check_level_testing_key
from shvatka.core.services.organizers import get_org_by_id
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.views.game import BotOrgNotifier
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.level_testing import create_level_test_view
from shvatka.tgbot.views.user import render_small_card_link
from .getters import get_level_and_org, get_org
from ... import keyboards as kb


async def edit_level(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer("TODO реализовать редактирование уровня")  # TODO


async def show_level(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    level_id = manager.start_data["level_id"]
    author: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    level = await get_by_id(level_id, author, dao.level)
    bot: Bot = manager.middleware_data["bot"]
    storage: FileStorage = manager.middleware_data["file_storage"]
    hint_resolver = HintContentResolver(dao=dao.file_info, file_storage=storage)
    hint_sender = HintSender(bot=bot, resolver=hint_resolver)
    asyncio.create_task(show_all_hints(author, hint_sender, bot, level))


async def show_all_hints(author: dto.Player, hint_sender: HintSender, bot: Bot, level: dto.Level):
    await bot.send_message(
        author.get_chat_id(), "Ключи уровня:\n🔑{}".format("\n🔑".join(level.scenario.keys))
    )
    for hint in level.scenario.time_hints:
        await hint_sender.send_hints(
            chat_id=author.get_chat_id(),
            hint_containers=hint.hint,
            caption=f"Подсказка {hint.time} мин.",
        )
    await hint_sender.bot.send_message(
        chat_id=author.get_chat_id(),
        text=f"Это был весь уровень {level.name_id}",
    )


async def send_to_testing(c: CallbackQuery, widget: Any, manager: DialogManager, org_id: str):
    dao: HolderDao = manager.middleware_data["dao"]
    bot: Bot = manager.middleware_data["bot"]
    author: dto.Player = manager.middleware_data["player"]
    level = await get_by_id(manager.start_data["level_id"], author, dao.level)
    org = await get_org_by_id(id_=int(org_id), dao=dao.organizer)
    await bot.send_message(
        chat_id=org.player.get_chat_id(),
        text=f"{render_small_card_link(author)} "
        f"предлагает протестировать уровень {level.name_id}. "
        f"Начать прямо сейчас?",
        reply_markup=kb.get_kb_level_test_invite(level, org),
    )
    await c.answer("Приглашение отправлено")


async def level_testing(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    scheduler: LevelTestScheduler = manager.middleware_data["scheduler"]
    dao: HolderDao = manager.middleware_data["dao"]
    bot: Bot = manager.middleware_data["bot"]
    storage: FileStorage = manager.middleware_data["file_storage"]
    level_id = manager.start_data["level_id"]
    author: dto.Player = manager.middleware_data["player"]
    level = await get_by_id(level_id, author, dao.level)
    org = await get_org(author, level, dao)
    suite = dto.LevelTestSuite(tester=org, level=level)
    view = create_level_test_view(bot=bot, dao=dao, storage=storage)
    await manager.start(state=states.LevelTestSG.wait_key, data={"level_id": level_id})
    await start_level_test(
        suite=suite, scheduler=scheduler, view=view, dao=dao.level_testing_complex
    )


async def unlink_level_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    dao: HolderDao = manager.middleware_data["dao"]
    level_id = manager.start_data["level_id"]
    author: dto.Player = manager.middleware_data["player"]
    level = await get_by_id(level_id, author, dao.level)
    await unlink_level(level, dao.level)
    await manager.done()


async def cancel_level_test(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    level, org = await get_level_and_org(author, dao, manager)
    suite = dto.LevelTestSuite(tester=org, level=level)
    await dao.level_test.cancel_test(suite=suite)
    await manager.done()


async def process_key_message(m: Message, dialog_: Any, manager: DialogManager) -> None:
    dao: HolderDao = manager.middleware_data["dao"]
    bot: Bot = manager.middleware_data["bot"]
    storage: FileStorage = manager.middleware_data["file_storage"]
    author: dto.Player = manager.middleware_data["player"]
    locker: KeyCheckerFactory = manager.middleware_data["locker"]
    level, org = await get_level_and_org(author, dao, manager)
    suite = dto.LevelTestSuite(tester=org, level=level)
    view = create_level_test_view(bot=bot, dao=dao, storage=storage)
    insert_result = await check_level_testing_key(
        key=typing.cast(str, m.text),
        suite=suite,
        view=view,
        org_notifier=BotOrgNotifier(bot=bot),
        locker=locker,
        dao=dao.level_testing_complex,
    )
    if insert_result.level_completed:
        await manager.done()


async def select_level_handler(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: int
):
    await manager.start(state=states.LevelManageSG.menu, data={"level_id": int(item_id)})
