from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Data, DialogManager
from aiogram_dialog.widgets.kbd import Button
from dataclass_factory import Factory

from shvatka.models.dto.scn import TimeHint
from tgbot.states import TimeHintSG


async def process_result(start_data: Data, result: Any, manager: DialogManager):
    if new_hint := result["time_hint"]:
        manager.dialog_data.setdefault("time_hints", []).append(new_hint)


async def start_add_time_hint(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dcf: Factory = manager.middleware_data["dcf"]
    hints = dcf.load(manager.dialog_data.get("time_hints", []), list[TimeHint])
    previous_time = hints[-1].time if hints else 0
    await manager.start(state=TimeHintSG.time, data={"previous_time": previous_time})
