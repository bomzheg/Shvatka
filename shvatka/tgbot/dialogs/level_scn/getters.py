from adaptix import Retort
from aiogram_dialog import DialogManager

from shvatka.core.models.dto import hints, scn


async def get_level_id(dialog_manager: DialogManager, **_):
    return {
        "level_id": dialog_manager.dialog_data.get("level_id", None)
        or dialog_manager.start_data["level_id"]
    }


async def get_keys(dialog_manager: DialogManager, **_):
    retort: Retort = dialog_manager.middleware_data["retort"]
    conditions = dialog_manager.dialog_data.get(
        "conditions", dialog_manager.start_data.get("conditions", [])
    )
    return {
        "keys": retort.load(conditions, scn.Conditions).get_keys(),
    }


async def get_bonus_keys(dialog_manager: DialogManager, **_):
    retort: Retort = dialog_manager.middleware_data["retort"]
    conditions = dialog_manager.dialog_data.get(
        "conditions", dialog_manager.start_data.get("conditions", [])
    )
    return {
        "bonus_keys": retort.load(conditions, scn.Conditions).get_bonus_keys(),
    }


async def get_level_data(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    retort: Retort = dialog_manager.middleware_data["retort"]
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    conditions_dumped = dialog_data.get(
        "conditions", dialog_manager.start_data.get("conditions", [])
    )
    conditions = retort.load(conditions_dumped, scn.Conditions)
    return {
        "level_id": dialog_data["level_id"],
        "bonus_keys": conditions.get_bonus_keys(),
        "keys": conditions.get_keys(),
        "time_hints": hints_,
    }


async def get_time_hints(dialog_manager: DialogManager, **_):
    dialog_data = dialog_manager.dialog_data
    retort: Retort = dialog_manager.middleware_data["retort"]
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    return {
        "level_id": dialog_manager.start_data["level_id"],
        "time_hints": hints_,
    }
