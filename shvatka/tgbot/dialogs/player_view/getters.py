from typing import Any

from aiogram_dialog import DialogManager

from shvatka.core.services.player import get_player_with_stat, get_teams_history
from shvatka.infrastructure.db.dao.holder import HolderDao


async def player_getter(dao: HolderDao, dialog_manager: DialogManager, **_) -> dict[str, Any]:
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    player_id: int = data["player_id"]
    player = await get_player_with_stat(player_id, dao.player)
    correct_keys_percent = (
        player.typed_correct_keys_count / player.typed_keys_count if player.typed_keys_count else 0
    )
    return {
        "player": player,
        "correct_keys": correct_keys_percent,
        "history": await get_teams_history(player, dao.team_player),
    }
