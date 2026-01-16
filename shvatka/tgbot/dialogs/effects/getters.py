from adaptix import Retort
from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.models.dto import hints


@inject
async def get_effects(
    dialog_manager: DialogManager,
    retort: Retort,
    **kwargs
):
    hints_: list[hints.AnyHint] = retort.load(
        dialog_manager.dialog_data["hints"], list[hints.AnyHint]
    )
    bonus: float = dialog_manager.dialog_data["bonus_minutes"]
    level_up: bool = dialog_manager.dialog_data["level_up"]
    routed_level_up: str | None = dialog_manager.dialog_data["next_level"]
    return {
        "bonus_minutes": bonus,
        "level_up": level_up,
        "next_level": routed_level_up,
        "hints": hints_,
    }

async def get_hints(dialog_manager: DialogManager, retort: Retort, **_):
    dialog_data = dialog_manager.dialog_data

    hints_ = retort.load(dialog_data["hints"], list[hints.AnyHint])
    return {
        "hints": hints_,
        "numerated_hints": list(enumerate(hints_)),
    }
