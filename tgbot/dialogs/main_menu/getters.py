from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import save_promotion_invite
from tgbot import keyboards as kb


async def get_player(dialog_manager: DialogManager, player: dto.Player, **_):
    return {
        "player": player,
    }


async def get_game(dialog_manager: DialogManager, game: dto.Game, **_):
    return {
        "game": game,
    }


async def get_promotion_token(dialog_manager: DialogManager, **_):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    token = await save_promotion_invite(player, dao.secure_invite)
    return {
        "player": player,
        "inline_query": kb.PromotePlayerID(token=token).pack(),
    }
