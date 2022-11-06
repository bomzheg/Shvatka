from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dataclass_factory import Factory

from shvatka.models.dto.scn import TimeHint
from shvatka.models.dto.scn.hint_part import AnyHint
from tgbot.states import TimeHintSG
from tgbot.views.hint_factory.hint_parser import HintParser


async def select_time(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    await set_time(int(item_id), manager)


async def process_time_message(m: Message, dialog_: Any, manager: DialogManager) -> None:
    try:
        time_ = int(m.text)
    except ValueError:
        await m.answer("Некорректный формат времени. Пожалуйста введите время в формате ЧЧ:ММ")
        return
    await set_time(time_, manager)


async def set_time(time_minutes: int, manager: DialogManager):
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["time"] = int(time_minutes)
    data["hints"] = []
    await manager.update(data)
    await manager.switch_to(TimeHintSG.hint)


async def process_hint(m: Message, dialog_: Any, manager: DialogManager) -> None:
    dcf: Factory = manager.middleware_data["dcf"]
    parser: HintParser = manager.middleware_data["hint_parser"]
    hint = await parser.parse(m, manager.middleware_data["player"])
    manager.dialog_data["hints"].append(dcf.dump(hint))


async def on_finish(c: CallbackQuery, button: Button, manager: DialogManager):
    dcf: Factory = manager.middleware_data["dcf"]
    await c.answer(str(len(manager.dialog_data["hints"])))
    hints = dcf.load(manager.dialog_data["hints"], list[AnyHint])
    time_ = manager.dialog_data["time"]
    time_hint = TimeHint(time=time_, hint=hints)
    await manager.done({"time_hint": dcf.dump(time_hint)})
