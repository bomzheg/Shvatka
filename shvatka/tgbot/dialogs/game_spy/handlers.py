from datetime import datetime

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.keys import create_keys_page
from shvatka.tgbot.views.telegraph import Telegraph


@inject
async def keys_handler(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
    telegraph: Telegraph,
):
    await c.answer()
    game: dto.Game = manager.middleware_data["game"]
    page = await create_keys_page(
        game=game, telegraph=telegraph, dao=dao, salt=game.manage_token[:8], identity=identity
    )
    manager.dialog_data["key_link"] = page["url"]
    manager.dialog_data["updated"] = datetime.now(tz=tz_utc).isoformat()
