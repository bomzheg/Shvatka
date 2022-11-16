from typing import Any

from aiogram.types import Message, CallbackQuery
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, ManagedMultiSelectAdapter

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import check_new_game_name_available, create_game, get_full_game, add_level
from shvatka.services.level import get_all_my_free_levels, get_by_id
from tgbot.states import LevelManageSG


async def process_name(m: Message, dialog_: Any, manager: DialogManager):
    if m.text.lower().strip() == "мудро":
        return await m.answer(
            "Лол, я ждал эту шутку. "
            "Но нет, игра не может называться {name}".format(name=hd.bold(m.text))
        )
    author: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    await check_new_game_name_available(name=m.text.strip(), author=author, dao=dao.game)
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["game_name"] = m.text
    await manager.update(data)
    await manager.next()


async def save_game(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    name: str = manager.dialog_data["game_name"]
    levels = await get_all_my_free_levels(author, dao.level)
    multiselect: ManagedMultiSelectAdapter = manager.find("my_level_ids")
    levels = list(filter(lambda l: multiselect.is_checked(l.db_id), levels))
    game = await create_game(author=author, name=name, dao=dao.game_creator, levels=levels)
    await c.message.edit_text("Игра успешно сохранена")
    await manager.done({"game": game})


async def edit_level(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    await manager.start(LevelManageSG.menu, data={"level_id": int(item_id)})


async def add_level_handler(c: CallbackQuery, button: Any, manager: DialogManager, item_id: str):
    await c.answer()
    game_id = manager.start_data["game_id"]
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    game = await get_full_game(game_id, author=author, dao=dao.game)
    level = await get_by_id(int(item_id), author=author, dao=dao.level)
    await add_level(game=game, level=level, author=author, dao=dao.level)
    await manager.done()

