from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from shvatka.core.models import dto
from shvatka.core.services.player import get_my_team, leave
from shvatka.infrastructure.db.dao.holder import HolderDao
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


async def on_leave_team(c: CallbackQuery, button: Button, dialog_manager: DialogManager):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    await leave(player, player, dao.team_leaver)
    await dialog_manager.done()


async def on_start_my_team(start_data: dict, manager: DialogManager) -> None:
    dao: HolderDao = manager.middleware_data["dao"]
    player: dto.Player = manager.middleware_data["player"]
    team = await get_my_team(player=player, dao=dao.team_player)
    assert team
    manager.dialog_data["team_id"] = team.id
