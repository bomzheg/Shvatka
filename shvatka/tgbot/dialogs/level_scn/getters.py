from aiogram_dialog import DialogManager
from dataclass_factory import Factory

from shvatka.core.models.dto import scn
from shvatka.core.models.dto.scn import TimeHint
from shvatka.tgbot.views.utils import render_time_hints


async def get_level_id(dialog_manager: DialogManager, **_):
    return {
        "level_id": dialog_manager.dialog_data.get("level_id", None)
        or dialog_manager.start_data["level_id"]
    }


async def get_keys(dialog_manager: DialogManager, **_):
    return {
        "keys": dialog_manager.dialog_data.get("keys", dialog_manager.start_data.get("keys", [])),
    }


async def get_bonus_keys(dialog_manager: DialogManager, **_):
    dcf: Factory = dialog_manager.middleware_data["dcf"]
    keys_raw = dialog_manager.dialog_data.get(
        "bonus_keys", dialog_manager.start_data.get("bonus_keys", [])
    )
    return {
        "bonus_keys": dcf.load(keys_raw, list[scn.BonusKey]),
    }


async def get_level_data(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    dcf: Factory = dialog_manager.middleware_data["dcf"]
    hints = dcf.load(dialog_data.get("time_hints", []), list[TimeHint])
    return {
        "level_id": dialog_data["level_id"],
        "keys": dialog_data.get("keys", []),
        "bonus_keys": dialog_data.get("bonus_keys", []),
        "time_hints": hints,
    }


async def get_time_hints(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    dcf: Factory = dialog_manager.middleware_data["dcf"]
    hints = dcf.load(dialog_data.get("time_hints", []), list[TimeHint])
    return {
        "level_id": dialog_manager.start_data["level_id"],
        "time_hints": hints,
    }
