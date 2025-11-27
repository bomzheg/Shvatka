from typing import Any

from adaptix import Retort
from aiogram.types import CallbackQuery
from aiogram_dialog import Data, DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject



@inject
async def on_start_timers(
    start_data: dict[str, Any], manager: DialogManager, retort: FromDishka[Retort]
):
    manager.dialog_data["level_id"] = start_data["level_id"]
    manager.dialog_data["game_id"] = start_data["game_id"]
    manager.dialog_data["conditions"] = start_data["conditions"]


@inject
async def save_timers(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.done(
        {
            "conditions": manager.dialog_data["conditions"],
        }
    )


async def process_timers_result(start_data: Data, result: Any, manager: DialogManager):
    if not result:
        return
