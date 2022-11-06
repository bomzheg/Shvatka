from aiogram_dialog import DialogManager
from dataclass_factory import Factory

from shvatka.models.dto.scn import TimeHint
from tgbot.views.utils import render_time_hints


async def get_time_hints(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    dcf: Factory = dialog_manager.middleware_data["dcf"]
    hints = dcf.load(dialog_data.get("time_hints", []), list[TimeHint])
    return {
        "time_hints": hints,
        "rendered": render_time_hints(hints),
    }
