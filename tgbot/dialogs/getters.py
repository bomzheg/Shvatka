from aiogram_dialog import DialogManager
from aiogram_dialog.context.context import Context
from aiogram_dialog.widgets.when import Whenable

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums import GameStatus
from shvatka.services import game
from shvatka.services.game import get_authors_games


async def get_my_games(dao: HolderDao, player: dto.Player, **_) -> dict[str, list[dto.Game]]:
    return {"games": await get_authors_games(player, dao.game)}


async def get_game(dao: HolderDao, player: dto.Player, aiogd_context: Context, **_):
    data = aiogd_context.dialog_data
    return {"game": await game.get_game(data["my_game_id"], player, dao.game)}


def already_getting_waivers(data: dict, widget: Whenable, manager: DialogManager):
    return data["game"].status in (GameStatus.underconstruction, GameStatus.ready)
