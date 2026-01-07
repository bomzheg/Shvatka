from aiogram_dialog import DialogManager
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.models.dto import hints


@inject
async def get_effects(dialog_manager: DialogManager, **kwargs):
    hints_: list[hints.AnyHint] = dialog_manager.dialog_data["hints"]
    bonus: float = dialog_manager.dialog_data["bonus_minutes"]
    level_up: bool = dialog_manager.dialog_data["level_up"]
    routed_level_up: str | None = dialog_manager.dialog_data["next_level"]
    return {
        "bonus_minutes": bonus,
        "level_up": level_up,
        "next_level": routed_level_up,
        "hints": hints_,
    }
