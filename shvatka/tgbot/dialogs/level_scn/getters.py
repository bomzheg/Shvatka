from adaptix import Retort
from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.models.dto import hints, action, scn


async def get_level_id(dialog_manager: DialogManager, **_):
    return {
        "level_id": dialog_manager.dialog_data.get("level_id", None)
        or dialog_manager.start_data["level_id"]
    }


async def get_keys(dialog_manager: DialogManager, **_):
    return {
        "keys": dialog_manager.dialog_data.get("keys", dialog_manager.start_data.get("keys", [])),
    }


@inject
async def get_bonus_keys(dialog_manager: DialogManager, retort: FromDishka[Retort], **_):
    keys_raw = dialog_manager.dialog_data.get("bonus_keys", [])
    return {
        "bonus_keys": retort.load(keys_raw, list[action.BonusKey]),
    }


@inject
async def get_level_data(dialog_manager: DialogManager, retort: FromDishka[Retort], **_):
    dialog_data = dialog_manager.dialog_data
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    if dumped_conditions := dialog_data["conditions"]:
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


@inject
async def get_time_hints(dialog_manager: DialogManager, retort: FromDishka[Retort], **_):
    dialog_data = dialog_manager.dialog_data
    hints_ = retort.load(dialog_data.get("time_hints", []), list[hints.TimeHint])
    return {
        "level_id": dialog_manager.start_data["level_id"],
        "time_hints": hints_,
    }


@inject
async def get_sly_keys(dialog_manager: DialogManager, retort: FromDishka[Retort], **_):
    data = dialog_manager.dialog_data
    return {
        "level_id": data["level_id"],
        "bonus_keys": retort.load(data["bonus_keys"], action.BonusKey),
        "bonus_hint_conditions": retort.load(
            data["bonus_hint_conditions"], list[action.KeyBonusHintCondition]
        ),
        "routed_conditions": retort.load(data["routed_conditions"], list[action.KeyWinCondition]),
        "game_id": data["game_id"],
    }
