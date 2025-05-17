from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services.game import get_full_game
from shvatka.core.services.level import get_all_my_free_levels
from shvatka.infrastructure.db.dao.holder import HolderDao


async def get_game_name(dialog_manager: DialogManager, **_):
    data = dialog_manager.dialog_data
    return {
        "game_name": data["game_name"],
    }


async def select_my_levels(dialog_manager: DialogManager, dao: HolderDao, **_):
    author: dto.Player = dialog_manager.middleware_data["player"]
    levels = await get_all_my_free_levels(author, dao.level)
    return {
        "levels": levels,
    }


@inject
async def select_full_game(
    dialog_manager: DialogManager,
    dao: HolderDao,
    identity: FromDishka[IdentityProvider],
    **_,
):
    id_: int = dialog_manager.start_data["game_id"]
    game = await get_full_game(id_, identity, dao.game)
    return {
        "levels": game.levels,
        "game": game,
    }
