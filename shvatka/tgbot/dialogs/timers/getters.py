from adaptix import Retort
from aiogram_dialog import DialogManager

from shvatka.core.models.dto import action


async def get_level_id(dialog_manager: DialogManager, **_):
    return {"level_id": dialog_manager.dialog_data.get("level_id", None)}


async def get_timers(dialog_manager: DialogManager, retort: Retort, **_):
    raw_conditions = dialog_manager.dialog_data.get("conditions", [])
    conditions = retort.load(raw_conditions, list[action.Condition])
    timers = [c for c in conditions if isinstance(c, action.LevelTimerEffectsCondition)]
    return {
        "timers": timers,
    }
