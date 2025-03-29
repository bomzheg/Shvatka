from adaptix import Retort
from aiogram_dialog import DialogManager

from shvatka.core.models.dto import hints, action, scn


async def get_level_id(dialog_manager: DialogManager, **_):
    return {
        "level_id": dialog_manager.dialog_data.get("level_id", None)
        or dialog_manager.start_data.get("level_id", None)
    }


async def get_keys(dialog_manager: DialogManager, **_):
    return {
        "keys": dialog_manager.dialog_data.get("keys", dialog_manager.start_data.get("keys", [])),
    }


async def get_bonus_keys(dialog_manager: DialogManager, retort: Retort, **_):
    keys_raw = dialog_manager.dialog_data.get("bonus_keys", [])
    return {
        "bonus_keys": retort.load(keys_raw, list[action.BonusKey]),
    }


async def get_level_data(dialog_manager: DialogManager, retort: Retort, **_):
    dialog_data = dialog_manager.dialog_data
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    if dumped_conditions := dialog_data.get("conditions", []):
        conditions = retort.load(dumped_conditions, scn.Conditions)
        sly_types_count = conditions.get_types_count()
    else:
        sly_types_count = 0
    return {
        "level_id": dialog_data["level_id"],
        "keys": dialog_data.get("keys", []),
        "sly_types": sly_types_count,
        "time_hints": hints_,
    }


async def get_time_hints(dialog_manager: DialogManager, retort: Retort, **_):
    dialog_data = dialog_manager.dialog_data
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    return {
        "level_id": dialog_manager.start_data["level_id"],
        "time_hints": hints_,
    }


async def get_sly_keys(dialog_manager: DialogManager, retort: Retort, **_):
    data = dialog_manager.dialog_data
    return {
        "level_id": data["level_id"],
        "bonus_keys": retort.load(data["bonus_keys"], list[action.BonusKey]),
        "bonus_hint_conditions": retort.load(
            data["bonus_hint_conditions"], list[action.KeyBonusHintCondition]
        ),
        "routed_conditions": retort.load(data["routed_conditions"], list[action.KeyWinCondition]),
        "game_id": data["game_id"],
    }


async def get_bonus_hint_conditions(dialog_manager: DialogManager, retort: Retort, **_):
    data = dialog_manager.dialog_data
    conditions = retort.load(data["bonus_hint_conditions"], list[action.KeyBonusHintCondition])
    return {
        "bonus_hint_conditions": dict(enumerate(conditions)),
        "game_id": data["game_id"],
    }


async def get_bonus_hints(dialog_manager: DialogManager, retort: Retort, **_):
    return {
        "hints": retort.load(dialog_manager.dialog_data["hints"], list[hints.AnyHint]),
    }
