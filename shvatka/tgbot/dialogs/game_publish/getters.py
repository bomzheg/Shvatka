from datetime import datetime

from aiogram_dialog import DialogManager

from shvatka.core.models import dto
from shvatka.core.services.game import get_game
from shvatka.infrastructure.db.dao.holder import HolderDao


async def get_org(dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **_):
    game_id = dialog_manager.start_data["game_id"]
    game = await get_game(id_=game_id, author=player, dao=dao.game)
    started = dialog_manager.dialog_data.get("started", None)
    started_at = dialog_manager.dialog_data.get("started_at", None)
    text_invite = dialog_manager.dialog_data.get("text_invite", None)
    return {
        "game": game,
        "player": player,
        "started": started,
        "started_at": datetime.fromisoformat(started_at) if started_at else None,
        "text_invite": text_invite,
    }
