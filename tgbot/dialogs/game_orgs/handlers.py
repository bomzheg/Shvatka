from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums.org_permission import OrgPermission
from shvatka.services.organizers import flip_permission, get_org_by_id, flip_deleted
from tgbot.states import GameOrgs


async def select_org(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    data = manager.dialog_data
    if data is None:
        data = {}
    data["org_id"] = int(item_id)
    await manager.switch_to(GameOrgs.org_menu)


async def change_permission_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    org_id = manager.dialog_data["org_id"]
    org = await get_org_by_id(org_id, dao.organizer)
    permission = OrgPermission[button.widget_id]
    await flip_permission(author, org, permission, dao.organizer)


async def change_deleted_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    org_id = manager.dialog_data["org_id"]
    org = await get_org_by_id(org_id, dao.organizer)
    await flip_deleted(author, org, dao.organizer)
