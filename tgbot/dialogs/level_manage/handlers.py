from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button


async def edit_level(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer("TODO реализовать редактирование уровня") # TODO

