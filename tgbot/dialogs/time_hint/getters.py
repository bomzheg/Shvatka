from aiogram_dialog import DialogManager
from dataclass_factory import Factory

from shvatka.models.dto.scn.hint_part import AnyHint
from tgbot.views.utils import render_hints


async def get_available_times(dialog_manager: DialogManager, **_):
    prev_time = int(dialog_manager.start_data.get("previous_time", 0))
    rounded = (prev_time // 5) * 5 + int((prev_time % 5) != 0) * 5
    return {"times": list(range(rounded, rounded + 5*8, 5))}


async def get_hints(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    dcf: Factory = dialog_manager.middleware_data["dcf"]

    hints = dcf.load(dialog_data["hints"], list[AnyHint])
    time_ = dialog_data["time"]
    return {
        "hints": hints,
        "time": time_,
        "has_hints": len(hints) > 0,
        "rendered": render_hints(hints),
    }
