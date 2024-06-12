from datetime import datetime

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.keys import create_keys_page
from shvatka.tgbot.views.telegraph import Telegraph


async def keys_handler(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    telegraph: Telegraph = manager.middleware_data["telegraph"]
    game: dto.Game = manager.middleware_data["game"]
    dao: HolderDao = manager.middleware_data["dao"]
    player: dto.Player = manager.middleware_data["player"]
    page = await create_keys_page(game, player, telegraph, dao, salt=game.manage_token[:8])
    manager.dialog_data["key_link"] = page["url"]
    manager.dialog_data["updated"] = datetime.now(tz=tz_utc).isoformat()
