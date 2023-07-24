from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Data, DialogManager
from aiogram_dialog.widgets.kbd import Button
from dataclass_factory import Factory

from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.services.level import upsert_level, get_by_id
from shvatka.core.utils.input_validation import (
    is_multiple_keys_normal,
    normalize_key,
    validate_level_id,
)
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states


def check_level_id(name_id: str) -> str:
    if value := validate_level_id(name_id):
        return value
    raise ValueError()


async def not_correct_id(m: Message, dialog_: Any, manager: DialogManager):
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


async def not_correct_keys(m: Message, dialog_: Any, manager: DialogManager):
    await m.answer(
        "Ключ должен начинаться на SH или СХ и содержать "
        "только цифры и заглавные буквы кириллицы и латиницы"
    )


async def on_correct_keys(m: Message, dialog_: Any, manager: DialogManager, keys: list[str]):
    await manager.done({"keys": keys})


async def process_time_hint_result(start_data: Data, result: Any, manager: DialogManager):
    if not result:
        return
    if new_hint := result["time_hint"]:
        manager.dialog_data.setdefault("time_hints", []).append(new_hint)


async def process_level_result(start_data: Data, result: Any, manager: DialogManager):
    if not result:
        return
    if hints := result.get("time_hints", None):
        manager.dialog_data["time_hints"] = hints
    if keys := result.get("keys", None):
        manager.dialog_data["keys"] = keys


async def on_start_level_edit(start_data: dict[str, Any], manager: DialogManager):
    dao: HolderDao = manager.middleware_data["dao"]
    dcf: Factory = manager.middleware_data["dcf"]
    author: dto.Player = manager.middleware_data["player"]
    level = await get_by_id(start_data["level_id"], author, dao.level)
    manager.dialog_data["level_id"] = level.name_id
    manager.dialog_data["keys"] = list(level.get_keys())
    manager.dialog_data["time_hints"] = dcf.dump(level.scenario.time_hints)


async def on_start_hints_edit(start_data: dict[str, Any], manager: DialogManager):
    manager.dialog_data["time_hints"] = start_data["time_hints"]


async def start_add_time_hint(c: CallbackQuery, button: Button, manager: DialogManager):
    dcf: Factory = manager.middleware_data["dcf"]
    hints = dcf.load(manager.dialog_data.get("time_hints", []), list[scn.TimeHint])
    previous_time = hints[-1].time if hints else -1
    await manager.start(state=states.TimeHintSG.time, data={"previous_time": previous_time})


async def start_hints(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=states.LevelHintsSG.time_hints,
        data={
            "level_id": manager.dialog_data["level_id"],
            "time_hints": manager.dialog_data.get("time_hints", []),
        },
    )


async def start_keys(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=states.LevelKeysSG.keys,
        data={
            "level_id": manager.dialog_data["level_id"],
            "keys": manager.dialog_data.get("keys", []),
        },
    )


async def save_hints(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.done({"time_hints": manager.dialog_data["time_hints"]})


async def clear_hints(c: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data.setdefault("time_hints", []).clear()


async def save_level(c: CallbackQuery, button: Button, manager: DialogManager):
    dcf: Factory = manager.middleware_data["dcf"]
    author: dto.Player = manager.middleware_data["player"]
    dao: HolderDao = manager.middleware_data["dao"]
    data = manager.dialog_data
    id_ = data["level_id"]
    keys = set(map(normalize_key, data["keys"]))
    time_hints = dcf.load(data["time_hints"], list[scn.TimeHint])

    level_scn = scn.LevelScenario(id=id_, keys=keys, time_hints=time_hints)
    level = await upsert_level(author=author, scenario=level_scn, dao=dao.level)
    await manager.done(result={"level": dcf.dump(level)})
    await c.answer(text="Уровень успешно сохранён")
