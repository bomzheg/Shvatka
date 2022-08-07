from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from app.states import MyGamesPanel


async def select_my_game(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    data = manager.current_context().start_data
    if not isinstance(data, dict):
        data = {}
    data["my_game_id"] = int(item_id)
    await manager.update(data)
    await manager.switch_to(MyGamesPanel.game_menu)
