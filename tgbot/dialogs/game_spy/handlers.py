from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from infrastructure.db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game_stat import get_typed_keys
from tgbot.views.keys import render_log_keys
from tgbot.views.telegraph import Telegraph


async def keys_handler(c: CallbackQuery, widget: Button, manager: DialogManager):
    await c.answer()
    telegraph: Telegraph = manager.middleware_data["telegraph"]
    game: dto.Game = manager.middleware_data["game"]
    dao: HolderDao = manager.middleware_data["dao"]
    player: dto.Player = manager.middleware_data["player"]
    keys = await get_typed_keys(game=game, player=player, dao=dao.key_time)
    text = render_log_keys(keys)
    page = await telegraph.create_page(
        title=f"Лог ключей игры {game.name}",
        html_content=text,
    )
    manager.dialog_data["key_link"] = page["url"]
