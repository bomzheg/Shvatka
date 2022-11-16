from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button


async def keys_handler(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
