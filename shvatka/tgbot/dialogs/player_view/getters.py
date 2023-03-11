from typing import Any

from aiogram_dialog import DialogManager

from shvatka.core.services.player import get_player_by_id
from shvatka.infrastructure.db.dao.holder import HolderDao


async def player_getter(dao: HolderDao, dialog_manager: DialogManager, **_) -> dict[str, Any]:
    player_id: int = dialog_manager.start_data["player_id"]
    player = await get_player_by_id(player_id, dao.player)
    return {
        "player": player,
    }
