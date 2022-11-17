from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.organizers import get_by_player


async def get_org(dao: HolderDao, player: dto.Player, game: dto.Game, dialog_manager: DialogManager, **_):
    org = await get_by_player(player=player, game=game, dao=dao.organizer)
    return {
        "game": game,
        "player": player,
        "org": org,
    }
