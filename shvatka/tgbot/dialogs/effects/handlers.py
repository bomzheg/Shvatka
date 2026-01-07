import uuid
from uuid import UUID

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
    manager.dialog_data["level_up"] = not manager.dialog_data["level_up"]


@inject
async def effects_on_start(start_data: dict, manager: DialogManager, retort: FromDishka[Retort]):
    effect_id: str = start_data.get("effect_id", str(uuid.uuid4()))
    hints_: list[hints.AnyHint] = start_data.get("hints", [])
    bonus: float = start_data.get("bonus_minutes", 0)
    level_up: bool = start_data.get("level_up", False)
    routed_level_up: str | None = start_data.get("next_level")
    manager.dialog_data["effect_id"] = effect_id
    manager.dialog_data["next_level"] = routed_level_up
    manager.dialog_data["bonus_minutes"] = bonus
    manager.dialog_data["level_up"] = level_up
    manager.dialog_data["hints"] = retort.dump(hints_, list[hints.AnyHint])


@inject
async def save_effects(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    await manager.done(
        {
            "effect_id": uuid.UUID(manager.dialog_data["effect_id"]),
            "next_level": manager.dialog_data["next_level"],
            "bonus_minutes": manager.dialog_data["bonus_minutes"],
            "level_up": manager.dialog_data["level_up"],
            "hints": retort.load(manager.dialog_data["hints"], list[hints.AnyHint]),
        }
    )
