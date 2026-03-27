from typing import Any

from adaptix import Retort
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Data, DialogManager, SubManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.models.dto import action, hints
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
    raw_condition = start_data.get("condition")
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


@inject
async def process_timers_result(
    start_data: Data, result: dict[str, Any], manager: DialogManager, retort: FromDishka[Retort]
):
    if not result:
        return
    assert isinstance(start_data, dict)
    if "condition" in start_data:
        raw_condition = start_data["condition"]
        if raw_condition is not None:
            condition = retort.load(raw_condition, action.LevelTimerEffectsCondition)
            for i, c in enumerate(  # noqa: B007
                retort.load(manager.dialog_data["conditions"], list[action.AnyCondition])
            ):
                if (
                    isinstance(c, action.LevelTimerEffectsCondition)
                    and c.action_time == condition.action_time
                ):
                    break
            else:
                raise RuntimeError("impossible! one of condition should be same")
            manager.dialog_data["conditions"][i] = retort.dump(result["condition"])
        else:
            manager.dialog_data["conditions"].append(retort.dump(result["condition"]))


@inject
async def start_edit_timer(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    assert isinstance(manager, SubManager)
    time = manager.item_id
    condition: action.LevelTimerEffectsCondition = next(  # type: ignore[assignment]
        filter(
            lambda x: hasattr(x, "action_time") and x.action_time == int(time),
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
async def delete_timer(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    assert isinstance(manager, SubManager)
    time = manager.item_id
    conditions: list[action.LevelTimerEffectsCondition] = list(
        filter(
            lambda x: getattr(x, "action_time", None) != int(time),
            retort.load(manager.dialog_data["conditions"], list[action.AnyCondition]),
        )
    )
    manager.dialog_data["conditions"] = retort.dump(conditions, list[action.AnyCondition])


@inject
async def start_new_timer(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    await manager.start(
        state=states.LevelTimerSG.menu,
        data={
            "condition": None,
            "level_id": manager.dialog_data["level_id"],
            "game_id": manager.dialog_data["game_id"],
        },
    )


@inject
async def start_effects(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    raw_effects = manager.dialog_data.get("effects", None)
    if raw_effects:
        effects: action.Effects = retort.load(raw_effects, action.Effects)
        data = {
            "effect_id": str(effects.id),
            "hints": retort.dump(effects.hints_, list[hints.AnyHint]),
            "bonus_minutes": effects.bonus_minutes,
            "level_up": effects.level_up,
            "next_level": effects.next_level,
            "level_id": manager.dialog_data.get("level_id", None),
            "game_id": manager.dialog_data.get("game_id", None),
        }
    else:
        data = {
            "level_id": manager.dialog_data.get("level_id", None),
            "game_id": manager.dialog_data.get("game_id", None),
        }
    await manager.start(
        state=states.EffectsSG.menu,
        data=data,
    )


async def process_incorrect_time_message(
    m: Message, widget: Any, manager: DialogManager, exception: ValueError
):
    await m.answer(
        "Некорректный формат времени. "
        "Пожалуйста введите время в формате целого числа - "
        "время с начала уровня в минутах (ММ), например 10"
    )


async def process_correct_time_message(m: Message, widget: Any, manager: DialogManager, data: int):
    await set_time(data, manager)


async def select_time(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await set_time(int(item_id), manager)


async def set_time(time_minutes: int, manager: DialogManager):
    manager.dialog_data["time"] = int(time_minutes)
    await manager.switch_to(state=states.LevelTimerSG.menu)


@inject
async def on_process_timer_result(
    start_data: Data,
    result: dict[str, Any],
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    if not result:
        return
    effect_id = result.get("effect_id")
    if effect_id:
        next_level: str | None = result.get("next_level")
        bonus_minutes: float = result.get("bonus_minutes", 0.0)
        level_up: bool = result.get("level_up", False)
        hints_: list[hints.AnyHint] = result.get("hints", [])
        manager.dialog_data["effects"] = retort.dump(
            action.Effects(
                id=effect_id,
                next_level=next_level,
                bonus_minutes=bonus_minutes,
                level_up=level_up,
                hints_=hints_,
            )
        )


@inject
async def save_timer(
    c: CallbackQuery, button: Button, manager: DialogManager, retort: FromDishka[Retort]
):
    await manager.done(
        {
            "condition": action.LevelTimerEffectsCondition(
                action_time=int(manager.dialog_data["time"]),
                effects=retort.load(manager.dialog_data["effects"], action.Effects),
            ),
        }
    )
