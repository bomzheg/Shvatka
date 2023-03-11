from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from shvatka.tgbot import states


async def select_team(c: CallbackQuery, widget: Any, manager: DialogManager, team_id: str):
    manager.dialog_data["team_id"] = int(team_id)
    await manager.switch_to(states.TeamsSg.one)


async def select_player(c: CallbackQuery, widget: Any, manager: DialogManager, player_id: str):
    await manager.start(states.PlayerSg.main, {"player_id": int(player_id)})
