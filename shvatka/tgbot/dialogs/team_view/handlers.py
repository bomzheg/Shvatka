from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.players.player import leave
from shvatka.core.views.team import TeamNotifier
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.dialogs.outdated import get_actual_team_player
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


@inject
async def on_leave_team(
    c: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    team_notifier: FromDishka[TeamNotifier],
):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player = (await get_actual_team_player(identity)).player
    await leave(player, player, dao.team_leaver, notifier=team_notifier)
    await dialog_manager.done()
