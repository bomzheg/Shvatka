from typing import Any, Sequence

from adaptix import Retort
from aiogram_dialog import DialogManager

from shvatka.core.models.dto import hints, action
from shvatka.core.models.dto.scn.level import (
    get_keys_default_condition,
)


async def get_level_id(dialog_manager: DialogManager, **_):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    return {"level_id": dialog_manager.dialog_data.get("level_id", None) or data.get("level_id")}


async def get_keys(dialog_manager: DialogManager, **_):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    return {
        "keys": dialog_manager.dialog_data.get("keys", data.get("keys", []) if data else []),
    }


async def get_level_data(dialog_manager: DialogManager, retort: Retort, **_):
    dialog_data = dialog_manager.dialog_data
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    dumped_conditions = dialog_data.get("conditions", [])
    conditions = retort.load(dumped_conditions, list[action.AnyCondition])
    effects_key = [c for c in conditions if isinstance(c, action.KeyEffectsCondition)]

    keys: set[action.SHKey] = get_keys_default_condition(conditions)
    timers: Sequence[action.LevelTimerEffectsCondition] = [
        condition
        for condition in conditions
        if isinstance(condition, action.LevelTimerEffectsCondition)
    ]
    win_timers = [t for t in timers if t.effects.level_up]
    return {
        "level_id": dialog_data["level_id"],
        "keys": keys,
        "timers": timers,
        "effects_key": effects_key,
        "win_timer": win_timers[0] if win_timers else None,
        "time_hints": hints_,
    }


async def get_time_hints(dialog_manager: DialogManager, retort: Retort, **_):
    dialog_data = dialog_manager.dialog_data
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    return {
        "level_id": data["level_id"],
        "time_hints": hints_,
    }


async def get_effects_conditions(dialog_manager: DialogManager, retort: Retort, **_):
    data = dialog_manager.dialog_data
    conditions = retort.load(data["effects_conditions"], list[action.KeyEffectsCondition])
    return {
        "effects_conditions": dict(enumerate(conditions)),
        "game_id": data["game_id"],
    }


async def get_effects_condition(dialog_manager: DialogManager, retort: Retort, **_):
    raw_effects = dialog_manager.dialog_data.get("effects", None)
    return {
        "keys": dialog_manager.dialog_data.get("keys", []),
        "effects": retort.load(raw_effects, action.Effects) if raw_effects else None,
    }
