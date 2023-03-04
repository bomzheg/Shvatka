from aiogram_dialog import DialogManager

from src.core.models import dto
from src.core.services.game_stat import get_game_spy
from src.core.services.organizers import get_by_player
from src.infrastructure.db.dao.holder import HolderDao


async def get_org(
    dao: HolderDao, player: dto.Player, game: dto.Game, dialog_manager: DialogManager, **_
):
    org = await get_by_player(player=player, game=game, dao=dao.organizer)
    return {
        "game": game,
        "player": player,
        "org": org,
    }


async def get_spy(
    dao: HolderDao, player: dto.Player, game: dto.Game, dialog_manager: DialogManager, **_
):
    stat = await get_game_spy(game, player, dao.game_stat)
    return {
        "stat": stat,
    }


async def get_keys(dialog_manager: DialogManager, **_):
    return {"key_link": dialog_manager.dialog_data.get("key_link", None)}
