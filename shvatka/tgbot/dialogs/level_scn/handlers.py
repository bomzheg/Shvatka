import typing
from typing import Any

from adaptix import Retort
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Data, DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.models import dto
from shvatka.core.models.dto import scn, action
from shvatka.core.models.dto import hints
from shvatka.core.services.level import upsert_level, get_by_id
from shvatka.core.utils.input_validation import (
    is_multiple_keys_normal,
    normalize_key,
    validate_level_id,
)
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser


def check_level_id(name_id: str) -> str:
    if value := validate_level_id(name_id):
        return value
    raise ValueError


async def not_correct_id(m: Message, dialog_: Any, manager: DialogManager, error: ValueError):
    await m.answer("Не стоит использовать ничего, кроме латинских букв, цифр, -, _")


async def process_id(m: Message, dialog_: Any, manager: DialogManager, name_id: str):
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    if await dao.level.is_name_id_exist(name_id, author):
        lvl = await dao.level.get_by_author_and_name_id(author, name_id)
        return await raise_restrict_rewrite_level(m, author, lvl, dao)
    manager.dialog_data["level_id"] = name_id
    await manager.next()


async def raise_restrict_rewrite_level(
    m: Message, author: dto.Player, lvl: dto.Level, dao: HolderDao
) -> None:
    game_error_msg = ""
    if lvl.game_id:
        game = await dao.game.get_by_id(lvl.game_id, author)
        game_error_msg = f" и используется в {game.name}"
    await m.answer(
        f"Этот id уровня уже занят тобой{game_error_msg}. "
        f"Для редактирования воспользуйся меню редактирования"
    )


def convert_keys(text: str) -> list[str]:
    keys = text.splitlines()
    if is_multiple_keys_normal(keys):
        return keys
    raise ValueError


async def not_correct_keys(m: Message, dialog_: Any, manager: DialogManager, error: ValueError):
    await m.answer(
        "Ключ должен начинаться на SH или СХ и содержать "
        "только цифры и заглавные буквы кириллицы и латиницы"
    )


async def on_correct_keys(m: Message, dialog_: Any, manager: DialogManager, keys: list[str]):
    await manager.done({"keys": keys})


def convert_bonus_keys(text: str) -> list[action.BonusKey]:
    result = []
    for key_str in text.splitlines():
        key, bonus = key_str.split(maxsplit=1)
        parsed_key = action.BonusKey(text=key, bonus_minutes=float(bonus))
        result.append(parsed_key)
    return result


async def not_correct_bonus_keys(
    m: Message, dialog_: Any, manager: DialogManager, error: ValueError
):
    await m.answer(
        "Ключ должен начинаться на SH или СХ и содержать "
        "только цифры и заглавные буквы кириллицы и латиницы. "
        "Значение бонуса - целое или дробное число с разумным значением"
    )


@inject
async def on_correct_bonus_keys(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    keys: list[action.BonusKey],
    retort: FromDishka[Retort],
):
    manager.dialog_data["bonus_keys"] = retort.dump(keys, list[action.BonusKey])


async def process_time_hint_result(start_data: Data, result: Any, manager: DialogManager):
    if not result:
        return
    if new_hint := result.get("time_hint", None):
        manager.dialog_data.setdefault("time_hints", []).append(new_hint)
    elif (edited_hint := result.get("edited_time_hint")) and isinstance(start_data, dict):
        old_hint = start_data["time_hint"]
        if edited_hint == old_hint:
            return
        retort: Retort = manager.middleware_data["retort"]
        hints_list = retort.load(manager.dialog_data.get("time_hints", []), scn.HintsList)
        if edited_hint.get("__deleted__") == "__deleted_true__":
            edited_list = hints_list.delete(retort.load(old_hint, hints.TimeHint))
        else:
            edited_list = hints_list.replace(
                retort.load(old_hint, hints.TimeHint), retort.load(edited_hint, hints.TimeHint)
            )
        manager.dialog_data["time_hints"] = retort.dump(edited_list)


async def process_level_result(start_data: Data, result: Any, manager: DialogManager):
    if not result:
        return
    if hints_ := result.get("time_hints", None):
        manager.dialog_data["time_hints"] = hints_
    if keys := result.get("keys", None):
        manager.dialog_data["keys"] = keys
    if bonus_keys := result.get("bonus_keys", None):
        manager.dialog_data["bonus_keys"] = bonus_keys
    if bonus_hint_conditions := result.get("bonus_hint_conditions", None):
        manager.dialog_data["bonus_hint_conditions"] = bonus_hint_conditions
    if routed_conditions := result.get("routed_conditions", None):
        manager.dialog_data["routed_conditions"] = routed_conditions


async def on_start_level_edit(start_data: dict[str, Any], manager: DialogManager):
    dao: HolderDao = manager.middleware_data["dao"]
    retort: Retort = manager.middleware_data["retort"]
    author: dto.Player = manager.middleware_data["player"]
    level = await get_by_id(start_data["level_id"], author, dao.level)
    manager.dialog_data["level_id"] = level.name_id
    manager.dialog_data["game_id"] = level.game_id
    manager.dialog_data["keys"] = list(
        level.scenario.conditions.get_default_key_condition().get_keys()
    )
    manager.dialog_data["time_hints"] = retort.dump(level.scenario.time_hints)
    manager.dialog_data["conditions"] = retort.dump(level.scenario.conditions)
    manager.dialog_data["bonus_keys"] = retort.dump(
        list(level.get_bonus_keys()), list[action.BonusKey]
    )


async def on_start_hints_edit(start_data: dict[str, Any], manager: DialogManager):
    manager.dialog_data["time_hints"] = start_data["time_hints"]


async def start_edit_time_hint(
    c: CallbackQuery, widget: Any, manager: DialogManager, hint_time: str
):
    retort: Retort = manager.middleware_data["retort"]
    hints_ = retort.load(manager.dialog_data.get("time_hints", []), list[hints.TimeHint])
    await manager.start(
        state=states.TimeHintEditSG.details,
        data={"time_hint": retort.dump(next(filter(lambda x: x.time == int(hint_time), hints_)))},
    )


async def start_add_time_hint(c: CallbackQuery, button: Button, manager: DialogManager):
    retort: Retort = manager.middleware_data["retort"]
    hints_ = retort.load(manager.dialog_data.get("time_hints", []), list[hints.TimeHint])
    previous_time = hints_[-1].time if hints_ else -1
    await manager.start(state=states.TimeHintSG.time, data={"previous_time": previous_time})


async def start_hints(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=states.LevelHintsSG.time_hints,
        data={
            "level_id": manager.dialog_data["level_id"],
            "time_hints": manager.dialog_data.get("time_hints", []),
        },
    )


async def start_level_keys(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=states.LevelKeysSG.keys,
        data={
            "level_id": manager.dialog_data["level_id"],
            "keys": manager.dialog_data.get("keys", []),
        },
    )


@inject
async def start_sly_keys(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=states.LevelSlyKeysSg.menu,
        data={
            "level_id": manager.dialog_data["level_id"],
            "bonus_keys": manager.dialog_data.get("bonus_keys", []),
            "conditions": manager.dialog_data.get("conditions", []),
            "keys": manager.dialog_data["keys"],
            "game_id": manager.dialog_data.get("game_id", None),
        },
    )


@inject
async def on_start_sly_keys(
    start_data: dict[str, Any], manager: DialogManager, retort: FromDishka[Retort]
):
    if dumped_conditions := start_data["conditions"]:
        conditions = retort.load(dumped_conditions, scn.Conditions)
    else:
        conditions = scn.Conditions([action.KeyWinCondition(start_data["keys"])])
    manager.dialog_data["level_id"] = start_data["level_id"]
    manager.dialog_data["keys"] = start_data["keys"]
    manager.dialog_data["bonus_keys"] = start_data["bonus_keys"]
    manager.dialog_data["conditions"] = retort.dump(conditions)
    manager.dialog_data["game_id"] = start_data["game_id"]
    manager.dialog_data["bonus_hint_conditions"] = retort.dump(
        conditions.get_bonus_hints_conditions(), list[action.KeyBonusHintCondition]
    )
    manager.dialog_data["routed_conditions"] = retort.dump(
        conditions.get_routed_conditions(), list[action.KeyWinCondition]
    )


@inject
async def save_sly_keys(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.done(
        {
            "bonus_keys": manager.dialog_data["bonus_keys"],
            "routed_conditions": manager.dialog_data["routed_conditions"],
            "bonus_hint_conditions": manager.dialog_data["bonus_hint_conditions"],
        }
    )


async def save_hints(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.done({"time_hints": manager.dialog_data["time_hints"]})


async def clear_hints(c: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data.setdefault("time_hints", []).clear()


async def save_level(c: CallbackQuery, button: Button, manager: DialogManager):
    retort: Retort = manager.middleware_data["retort"]
    author: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    data = manager.dialog_data
    id_ = data["level_id"]
    keys = set(map(normalize_key, data["keys"]))
    time_hints = retort.load(data["time_hints"], list[hints.TimeHint])
    bonus_keys = retort.load(data.get("bonus_keys", []), set[action.BonusKey])
    routed_conditions = retort.load(
        data.get("routed_conditions", []), list[action.KeyWinCondition]
    )
    bonus_hint_conditions = retort.load(
        data.get("bonus_hint_conditions", []), list[action.KeyBonusHintCondition]
    )
    if dumped_condition := data.get("conditions", None):
        conditions = retort.load(dumped_condition, scn.Conditions)
        conditions = (
            conditions.replace_default_keys(keys)
            .replace_bonus_keys(bonus_keys)
            .replace_bonus_hints_conditions(bonus_hint_conditions)
            .replace_routed_conditions(routed_conditions)
        )
    else:
        conditions = scn.Conditions(
            [
                action.KeyWinCondition(keys),
                action.KeyBonusCondition(bonus_keys),
                *routed_conditions,
                *bonus_hint_conditions,
            ]
        )

    level_scn = scn.LevelScenario(
        id=id_,
        time_hints=time_hints,
        conditions=conditions,
        __model_version__=1,
    )
    level = await upsert_level(author=author, scenario=level_scn, dao=dao.level)
    await manager.done(result={"level": retort.dump(level)})
    await c.answer(text="Уровень успешно сохранён")


async def start_bonus_hint_keys(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=states.LevelKeysSG.keys,
        data={
            "keys": manager.dialog_data.get("keys", []),
        },
    )


@inject
async def process_hint(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    retort: FromDishka[Retort],
    parser: FromDishka[HintParser],
) -> None:
    hint = await parser.parse(m, manager.middleware_data["player"])
    manager.dialog_data["hints"].append(retort.dump(hint))


@inject
async def edit_bonus_hint(
    c: CallbackQuery, widget: Any, manager: DialogManager, number: str, retort: FromDishka[Retort]
):
    data = manager.dialog_data
    conditions = dict(
        enumerate(retort.load(data["bonus_hint_conditions"], list[action.KeyBonusHintCondition]))
    )
    to_edit: action.KeyBonusHintCondition = conditions[int(number)]
    await manager.start(
        state=states.BonusHintSg.menu,
        data={
            "edited_bonus_hint_condition": int(number),
            "keys": retort.dump(to_edit.keys, list[str]),
            "hints": retort.dump(to_edit.bonus_hint, list[hints.AnyHint]),
        },
    )


async def on_start_bonus_hints_edit(start_data: dict[str, Any], manager: DialogManager):
    if start_data is None:
        start_data = {}
    manager.dialog_data["hints"] = start_data.get("hints", [])
    manager.dialog_data["keys"] = start_data.get("keys", [])


@inject
async def save_bonus_hint(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    conditions = action.KeyBonusHintCondition(
        keys=manager.dialog_data["keys"],
        bonus_hint=retort.load(manager.dialog_data["hints"], list[hints.AnyHint]),
    )
    await manager.done({"bonus_hint_condition": conditions})


@inject
async def process_sly_keys_result(
    start_data: Data, result: Any, manager: DialogManager, retort: FromDishka[Retort]
):
    if not result:
        return
    if bonus_hint_condition := result.get("bonus_hint_condition", None):
        c = retort.load(
            manager.dialog_data["bonus_hint_conditions"], list[action.KeyBonusHintCondition]
        )
        start_data = typing.cast(dict[str, Any], start_data)
        if (number := start_data.get("edited_bonus_hint_condition", None)) is not None:
            c[int(number)] = bonus_hint_condition
        else:
            c.append(bonus_hint_condition)
        manager.dialog_data["bonus_hint_conditions"] = retort.dump(
            c, list[action.KeyBonusHintCondition]
        )


async def process_bonus_hint_result(start_data: Data, result: Any, manager: DialogManager):
    if not result:
        return
    if keys := result.get("keys", None):
        manager.dialog_data["keys"] = keys
