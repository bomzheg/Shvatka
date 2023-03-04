from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Data, DialogManager
from aiogram_dialog.widgets.kbd import Button
from dataclass_factory import Factory

from src.infrastructure.db.dao.holder import HolderDao
from src.shvatka.models import dto
from src.shvatka.models.dto import scn
from src.shvatka.services.level import upsert_level
from src.shvatka.utils.input_validation import (
    is_level_id_correct,
    is_multiple_keys_normal,
    normalize_key,
)
from src.tgbot import states


async def process_id(m: Message, dialog_: Any, manager: DialogManager):
    if not is_level_id_correct(m.text):
        await m.answer("Не стоит использовать ничего, кроме латинских букв, цифр, -, _")
        return
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["level_id"] = m.text
    await manager.next()


async def process_keys(m: Message, dialog_: Any, manager: DialogManager):
    keys = m.text.splitlines()
    if not is_multiple_keys_normal(keys):
        await m.answer(
            "Ключ должен начинаться на SH или СХ и содержать "
            "только цифры и заглавные буквы кириллицы и латиницы"
        )
        return
    data = manager.dialog_data
    data["keys"] = keys
    await manager.next()


async def process_result(start_data: Data, result: Any, manager: DialogManager):
    if not result:
        return
    if new_hint := result["time_hint"]:
        manager.dialog_data.setdefault("time_hints", []).append(new_hint)


async def start_add_time_hint(c: CallbackQuery, button: Button, manager: DialogManager):
    dcf: Factory = manager.middleware_data["dcf"]
    hints = dcf.load(manager.dialog_data.get("time_hints", []), list[scn.TimeHint])
    previous_time = hints[-1].time if hints else -1
    await manager.start(state=states.TimeHintSG.time, data={"previous_time": previous_time})


async def save_level(c: CallbackQuery, button: Button, manager: DialogManager):
    dcf: Factory = manager.middleware_data["dcf"]
    author: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    data = manager.dialog_data
    id_ = data["level_id"]
    keys = set(map(normalize_key, data["keys"]))
    time_hints = dcf.load(manager.dialog_data["time_hints"], list[scn.TimeHint])

    level_scn = scn.LevelScenario(id=id_, keys=keys, time_hints=time_hints)
    level = await upsert_level(author=author, scenario=level_scn, dao=dao.level)
    await manager.done(result={"level": dcf.dump(level)})
    await c.answer(text="Уровень успешно сохранён")
