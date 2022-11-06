from aiogram_dialog import DialogManager
from dataclass_factory import Factory

from shvatka.models.dto.scn import TimeHint


async def get_time_hints(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    dcf: Factory = dialog_manager.middleware_data["dcf"]
    hints = dcf.load(dialog_data.get("time_hints", []), list[TimeHint])
    print(hints)
    return {
        "time_hints": hints,
        "time_hints_count": len(hints),
    }
