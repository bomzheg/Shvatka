import logging
import typing
from typing import Any
from zipfile import Path as ZipPath

from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, ManagedMultiSelectAdapter
from dataclass_factory import Factory

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.models.dto import scn  # noqa: F401
from shvatka.core.services.achievement import add_achievement
from shvatka.core.services.game import (
    check_new_game_name_available,
    create_game,
    get_full_game,
    add_level,
    upsert_game,
)
from shvatka.core.services.level import get_all_my_free_levels, get_by_id
from shvatka.core.services.scenario.scn_zip import unpack_scn
from shvatka.core.utils.exceptions import ScenarioNotCorrect
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states

logger = logging.getLogger(__name__)


async def process_name(m: Message, dialog_: Any, manager: DialogManager):
    author: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    if m.text.lower().strip() == "мудро":
        await add_achievement(
            player=author, name=enums.Achievement.game_name_joke, dao=dao.achievement
        )
        return await m.answer(
            "Лол, я ждал эту шутку. "
            "Но нет, игра не может называться {name}".format(name=hd.bold(m.text))
        )
    await check_new_game_name_available(name=m.text.strip(), author=author, dao=dao.game)
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["game_name"] = m.text
    await manager.next()


async def process_zip_scn(m: Message, dialog_: Any, manager: DialogManager):
    player: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    bot: Bot = manager.middleware_data["bot"]
    file_gateway: FileGateway = manager.middleware_data["file_gateway"]
    dcf: Factory = manager.middleware_data["dcf"]
    document = await bot.download(m.document.file_id)
    try:
        with unpack_scn(ZipPath(document)).open() as scenario:  # type: scn.RawGameScenario
            game = await upsert_game(scenario, player, dao.game_upserter, dcf, file_gateway)
    except ScenarioNotCorrect as e:
        await m.reply(f"Ошибка {e}\n попробуйте исправить файл")
        logger.error("game scenario from player %s has problems", player.id, exc_info=e)
        return
    await m.reply("Успешно сохранено")
    await manager.done(result={"game": game})


async def save_game(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    name: str = manager.dialog_data["game_name"]
    levels = await get_all_my_free_levels(author, dao.level)
    multiselect = typing.cast(ManagedMultiSelectAdapter, manager.find("my_level_ids"))
    levels = list(filter(lambda level: multiselect.is_checked(level.db_id), levels))
    game = await create_game(author=author, name=name, dao=dao.game_creator, levels=levels)
    await c.message.edit_text("Игра успешно сохранена")
    await manager.done(result={"game": game})


async def edit_level(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    await manager.start(states.LevelManageSG.menu, data={"level_id": int(item_id)})


async def add_level_handler(c: CallbackQuery, button: Any, manager: DialogManager, item_id: str):
    await c.answer()
    game_id = manager.start_data["game_id"]
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    game = await get_full_game(game_id, author=author, dao=dao.game)
    level = await get_by_id(int(item_id), author=author, dao=dao.level)
    await add_level(game=game, level=level, author=author, dao=dao.level)
    await manager.done()
