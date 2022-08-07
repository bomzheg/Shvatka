from aiogram_dialog.context.context import Context

from app.dao.holder import HolderDao
from app.models import dto
from app.services import game
from app.services.game import get_authors_games


async def get_my_games(dao: HolderDao, player: dto.Player, **_) -> dict[str, list[dto.Game]]:
    return {
        "games": await get_authors_games(player, dao.game),
    }


async def get_game(dao: HolderDao, player: dto.Player, aiogd_context: Context, **_):
    data = aiogd_context.dialog_data
    return {"game": await game.get_game(data["my_game_id"], player, dao.game)}
