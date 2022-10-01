from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db.dao import GameDao
from shvatka.models import dto
from shvatka.services import game
from shvatka.services.game import get_game
from tgbot.states import MyGamesPanel


async def select_my_game(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    data = manager.current_context().start_data
    if not isinstance(data, dict):
        data = {}
    data["my_game_id"] = int(item_id)
    await manager.update(data)
    await manager.switch_to(MyGamesPanel.game_menu)


async def start_waivers(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    context_data = manager.data
    data = manager.current_context().dialog_data
    player: dto.Player = context_data["player"]
    game_dao: GameDao = context_data["dao"].game
    game_ = await get_game(int(data["my_game_id"]), player, game_dao)
    await game.start_waivers(game_, player, game_dao)
