import math
import uuid
from typing import Any

from adaptix import Retort
from aiogram import types
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, SubManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.services.game import get_full_game
from shvatka.core.utils.input_validation import validate_level_id
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.hint_sender import HintSender


async def process_level_up_change(
    callback_query: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    manager.dialog_data["level_up"] = not manager.dialog_data["level_up"]


@inject
async def effects_on_start(start_data: dict, manager: DialogManager):
    effect_id: str = start_data.get("effect_id", str(uuid.uuid4()))
    hints_: list[hints.AnyHint] = start_data.get("hints", [])
    bonus: float = start_data.get("bonus_minutes", 0)
    level_up: bool = start_data.get("level_up", False)
    routed_level_up: str | None = start_data.get("next_level")
    level_id: str | None = start_data.get("level_id")
    game_id: str | None = start_data.get("game_id")
    manager.dialog_data["effect_id"] = effect_id
    manager.dialog_data["next_level"] = routed_level_up
    manager.dialog_data["bonus_minutes"] = bonus
    manager.dialog_data["level_up"] = level_up
    manager.dialog_data["hints"] = hints_
    manager.dialog_data["level_id"] = level_id
    manager.dialog_data["game_id"] = game_id


@inject
async def save_effects(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    await manager.done(
        {
            "effect_id": uuid.UUID(manager.dialog_data["effect_id"]),
            "next_level": manager.dialog_data["next_level"],
            "bonus_minutes": manager.dialog_data["bonus_minutes"],
            "level_up": manager.dialog_data["level_up"],
            "hints": retort.load(manager.dialog_data["hints"], list[hints.AnyHint]),
        }
    )


@inject
async def show_single_hint(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    retort: FromDishka[Retort],
    hint_sender: FromDishka[HintSender],
):
    assert isinstance(manager, SubManager)
    hint = retort.load(manager.dialog_data["hints"], list[hints.AnyHint])
    chat: types.Chat = manager.middleware_data["event_chat"]
    hint_index = manager.item_id
    await hint_sender.send_hint(hint[int(hint_index)], chat.id)


@inject
async def delete_single_hint(
    c: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    retort: FromDishka[Retort],
):
    assert isinstance(manager, SubManager)
    hints_ = retort.load(manager.dialog_data.get("hints"), list[hints.AnyHint])
    hint_index = manager.item_id
    hints_.pop(int(hint_index))
    manager.dialog_data["hints"] = retort.dump(hints_, list[hints.AnyHint])


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
async def save_new_bonus(m: Message, dialog_: Any, manager: DialogManager, data: float) -> None:
    if (
        math.isnan(data)
        or math.isinf(data)
        or math.fabs(data) > 10000
        or (math.fabs(data) < 0.01 and data != 0)
    ):
        await m.reply(
            "Нужно ввести любое число, "
            "принимаются целые и дробные числа с разделителем '.': "
            "например '5', '-3', '0.2'.\n"
            "ℹ️Похоже ты ввёл слишком большое или слишком маленькое число (или вовсе не число)"
        )
        return
    manager.dialog_data["bonus_minutes"] = data


@inject
async def wrong_bonus_value(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    error: ValueError,
) -> None:
    await m.reply(
        "Нужно ввести любое число, "
        "принимаются целые и дробные числа с разделителем '.': "
        "например '5', '-3', '0.2'"
    )


@inject
async def process_routed_level_id(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    name_id: str,
    dao: FromDishka[HolderDao],
    identity: FromDishka[IdentityProvider],
):
    game = await get_full_game(manager.dialog_data["game_id"], identity, dao.game)
    ids = {lvl.name_id for lvl in game.levels}
    if name_id not in ids:
        await m.reply(
            "Введённый id не соответствует ни одному из уровней в игре. "
            "В игре сейчас следующие уровни: " + ", ".join(ids)
        )
        return
    manager.dialog_data["next_level"] = name_id
    await manager.switch_to(state=states.EffectsSG.menu)


async def not_correct_id(m: Message, dialog_: Any, manager: DialogManager, error: ValueError):
    await m.answer("Не стоит использовать ничего, кроме латинских букв, цифр, -, _")


def check_level_id(name_id: str) -> str:
    if value := validate_level_id(name_id):
        return value
    raise ValueError
