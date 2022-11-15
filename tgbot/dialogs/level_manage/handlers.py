import asyncio

from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.scheduler import LevelTestScheduler
from shvatka.services.game import get_game
from shvatka.services.level import get_by_id
from shvatka.services.level_testing import start_level_test
from shvatka.services.organizers import get_primary_orgs
from tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from tgbot.views.hint_sender import HintSender
from tgbot.views.level_testing import create_level_test_view


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
    asyncio.create_task(show_all_hints(author, hint_sender, level))


async def show_all_hints(author: dto.Player, hint_sender: HintSender, level: dto.Level):
    for hint in level.scenario.time_hints:
        await hint_sender.send_hints(
            chat_id=author.user.tg_id,
            hint_containers=hint.hint,
            caption=f"Подсказка {hint.time} мин.",
        )
    await hint_sender.bot.send_message(
        chat_id=author.user.tg_id,
        text=f"Это был весь уровень {level.name_id}",
    )


async def level_testing(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    scheduler: LevelTestScheduler = manager.middleware_data["scheduler"]
    dao: HolderDao = manager.middleware_data["dao"]
    bot: Bot = manager.middleware_data["bot"]
    storage: FileStorage = manager.middleware_data["file_storage"]
    level_id = manager.start_data["level_id"]
    author: dto.Player = manager.middleware_data["player"]
    level = await get_by_id(level_id, author, dao.level)
    game = await get_game(level.game_id, author=author, dao=dao.game)
    orgs = await get_primary_orgs(game)
    assert orgs[0].player.id == author.id
    assert 1 == len(orgs)
    suite = dto.LevelTestSuite(tester=orgs[0], level=level)
    view = create_level_test_view(bot=bot, dao=dao, storage=storage)
    await start_level_test(suite=suite, scheduler=scheduler, view=view, dao=dao.level_test)
