from adaptix import Retort
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.models.dto import hints


async def process_level_up_change(
    callback_query: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    manager.dialog_data["level_up_change"] = not manager.dialog_data["level_up_change"]


@inject
async def effects_on_start(start_data: dict, manager: DialogManager, retort: FromDishka[Retort]):
    hints_: list[hints.AnyHint] = start_data.get("hints", [])
    bonus: float = start_data.get("bonus", 0)
    level_up: bool = start_data.get("level_up", False)
    routed_level_up: str | None = start_data.get("routed_level_up")
    manager.dialog_data["routed_level_up"] = routed_level_up
    manager.dialog_data["bonus"] = bonus
    manager.dialog_data["level_up"] = level_up
    manager.dialog_data["hints"] = retort.dump(hints_)


@inject
async def save_effects(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    await manager.done(
        {
            "routed_level_up": manager.dialog_data["routed_level_up"],
            "bonus": manager.dialog_data["bonus"],
            "level_up": manager.dialog_data["level_up"],
            "hints": retort.load(manager.dialog_data["hints"], list[hints.AnyHint]),
        }
    )
