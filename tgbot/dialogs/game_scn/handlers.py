from typing import Any

from aiogram.types import Message, CallbackQuery
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Multiselect

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import check_new_game_name_available
from shvatka.services.level import get_all_my_levels


async def process_name(m: Message, dialog_: Any, manager: DialogManager):
    if m.text.lower().strip() == "мудро":
        return await m.answer(
            "Лол, я ждал эту шутку. "
            "Но нет, игра не может называться {name}".format(name=hd.bold(m.text))
        )
    author: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    await check_new_game_name_available(name=m.text, author=author, dao=dao.game)
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
    levels = await get_all_my_levels(author, dao.level)
    multiselect: Multiselect = manager.find("my_level_ids")
    for level in levels:
        print(multiselect.is_checked(level.db_id, manager))

