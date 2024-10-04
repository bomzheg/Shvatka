from adaptix import Retort
from aiogram_dialog import DialogManager
from dataclass_factory import Factory

from shvatka.core.models.dto.scn.hint_part import AnyHint


async def get_available_times(dialog_manager: DialogManager, **_):
    prev_time = int(dialog_manager.start_data.get("previous_time", 0))
    if prev_time == -1:
        # in case of no hints first value in most case must be 0 (puzzle)
        times = [0]
    else:
        rounded = (prev_time // 5) * 5 + 5
        times = list(range(rounded, rounded + 5 * 12, 5))
    return {"times": times}


async def get_hints(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    retort: Retort = dialog_manager.middleware_data["retort"]

    hints = retort.load(dialog_data["hints"], list[AnyHint])
    time_ = dialog_data["time"]
    return {
        "hints": hints,
        "numerated_hints": list(enumerate(hints)),
        "time": time_,
        "has_hints": len(hints) > 0,
    }
