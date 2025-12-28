from typing import Any

from adaptix import Retort
from aiogram.types import CallbackQuery
from aiogram_dialog import Data, DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.models.dto import action
from shvatka.tgbot import states


@inject
async def on_start_timers(
    start_data: dict[str, Any], manager: DialogManager, retort: FromDishka[Retort]
):
    manager.dialog_data["level_id"] = start_data["level_id"]
    manager.dialog_data["game_id"] = start_data["game_id"]
    manager.dialog_data["conditions"] = start_data["conditions"]


@inject
async def on_start_timer(
    start_data: dict[str, Any], manager: DialogManager, retort: FromDishka[Retort]
):
    manager.dialog_data["level_id"] = start_data["level_id"]
    manager.dialog_data["game_id"] = start_data["game_id"]
    raw_condition = start_data.get("condition", None)
    if raw_condition:
        condition = retort.load(raw_condition, action.AnyCondition)
        assert isinstance(condition, action.LevelTimerEffectsCondition)
        manager.dialog_data["time"] = condition.action_time
        manager.dialog_data["effects"] = retort.dump(condition.effects)
    else:
        manager.dialog_data["time"] = None
        manager.dialog_data["effects"] = None


@inject
async def save_timers(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.done(
        {
            "conditions": manager.dialog_data["conditions"],
        }
    )


async def process_timers_result(start_data: Data, result: Any, manager: DialogManager):
    if not result:
        return


@inject
async def start_edit_timer(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    time: int,
    retort: FromDishka[Retort],
):
    condition: action.LevelTimerEffectsCondition = next(  # type: ignore[assignment]
        filter(
            lambda x: hasattr(x, "action_time") and x.action_time == time,
            retort.load(manager.dialog_data["conditions"], list[action.AnyCondition]),
        )
    )
    await manager.start(
        state=states.LevelTimerSG.menu,
        data={
            "condition": retort.dump(condition),
            "level_id": manager.dialog_data["level_id"],
            "game_id": manager.dialog_data["game_id"],
        },
    )



@inject
async def start_new_timer(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
):

    await manager.start(
        state=states.LevelTimerSG.menu,
        data={
            "condition": None,
            "level_id": manager.dialog_data["level_id"],
            "game_id": manager.dialog_data["game_id"],
        },
    )
