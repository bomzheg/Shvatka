from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from shvatka.tgbot import states
from shvatka.tgbot.dialogs.team_view.common import get_active_filter, get_archive_filter


async def select_team(c: CallbackQuery, widget: Any, manager: DialogManager, team_id: str):
    manager.dialog_data["team_id"] = int(team_id)
    await manager.switch_to(states.TeamsSg.one)


async def select_player(c: CallbackQuery, widget: Any, manager: DialogManager, player_id: str):
    await manager.start(states.PlayerSg.main, {"player_id": int(player_id)})


async def change_active_filter(c: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["active"] = not get_active_filter(manager)


async def change_archive_filter(c: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data[button.widget_id] = not get_archive_filter(manager)
