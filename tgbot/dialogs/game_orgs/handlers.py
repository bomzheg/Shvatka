from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager


async def select_org(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer("TODO")  # TODO
