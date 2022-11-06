from aiogram_dialog import DialogManager
from dataclass_factory import Factory

from shvatka.models.dto.scn.hint_part import AnyHint

TIMES_PRESET = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]


async def get_available_times(dialog_manager: DialogManager, **_):
    prev_time = int(dialog_manager.start_data.get("previous_time", 0))
    return {"times": filter(lambda t: t > prev_time, TIMES_PRESET)}


async def get_hints(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    dcf: Factory = dialog_manager.middleware_data["dcf"]

    hints = dcf.load(dialog_data["hints"], list[AnyHint])
    time_ = dialog_data["time"]
    return {
        "hints": hints,
        "time": time_,
        "has_hints": len(hints) > 0,
        "hints_count": len(hints),
    }
