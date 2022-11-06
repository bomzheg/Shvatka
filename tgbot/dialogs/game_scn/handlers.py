from typing import Any

from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import check_new_game_name_available
from shvatka.utils.input_validation import is_level_id_correct


async def process_name(m: Message, dialog_: Any, manager: DialogManager):
    if not is_level_id_correct(m.text):
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
