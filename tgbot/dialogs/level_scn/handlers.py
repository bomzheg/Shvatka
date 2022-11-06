from typing import Any

from aiogram_dialog import Data, DialogManager


async def process_result(start_data: Data, result: Any, manager: DialogManager):
    if new_hint := result["time_hint"]:
        manager.dialog_data.setdefault("time_hints", []).append(new_hint)
