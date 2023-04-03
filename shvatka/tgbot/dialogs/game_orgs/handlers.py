from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from shvatka.core.models import dto
from shvatka.core.models.enums.org_permission import OrgPermission
from shvatka.core.services.organizers import flip_permission, get_org_by_id, flip_deleted
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states


async def select_org(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await c.answer()
    data = manager.dialog_data
    if data is None:
        data = {}
    data["org_id"] = int(item_id)
    await manager.switch_to(states.GameOrgsSG.org_menu)


async def change_permission_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    org_id = manager.dialog_data["org_id"]
    org = await get_org_by_id(org_id, dao.organizer)
    assert button.widget_id
    permission = OrgPermission[button.widget_id]
    try:
        await flip_permission(author, org, permission, dao.organizer)
    except exceptions.GameHasAnotherAuthor:
        await c.answer("разрешён только просмотр")


async def change_deleted_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    author: dto.Player = manager.middleware_data["player"]
    org_id = manager.dialog_data["org_id"]
    org = await get_org_by_id(org_id, dao.organizer)
    try:
        await flip_deleted(author, org, dao.organizer)
    except exceptions.GameHasAnotherAuthor:
        await c.answer("разрешён только просмотр")
