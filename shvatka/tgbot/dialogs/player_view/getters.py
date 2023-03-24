from typing import Any

from aiogram_dialog import DialogManager

from shvatka.core.services.player import get_player_with_stat
from shvatka.infrastructure.db.dao.holder import HolderDao


async def player_getter(dao: HolderDao, dialog_manager: DialogManager, **_) -> dict[str, Any]:
    player_id: int = dialog_manager.start_data["player_id"]
    player = await get_player_with_stat(player_id, dao.player)
    return {
        "player": player,
        "game_numbers": list(map(str, player.played_games)),
        "correct_keys": player.typed_correct_keys_count / player.typed_keys_count,
    }
