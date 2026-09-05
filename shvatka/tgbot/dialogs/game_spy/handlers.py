from datetime import datetime

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.complex import TypedKeyGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.tgbot.views.keys import create_keys_page
from shvatka.tgbot.views.telegraph import Telegraph


@inject
async def keys_handler(
    c: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    telegraph: FromDishka[Telegraph],
    typed_keys: FromDishka[TypedKeyGetter],
    current_game: FromDishka[CurrentGameProvider],
):
    game = await current_game.get_required_game()
    page = await create_keys_page(
        game=game,
        telegraph=telegraph,
        dao=typed_keys,
        salt=game.manage_token[:8],
        identity=identity,
    )
    manager.dialog_data["key_link"] = page["url"]
    manager.dialog_data["updated"] = datetime.now(tz=tz_utc).isoformat()
