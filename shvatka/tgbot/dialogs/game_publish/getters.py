from datetime import datetime
from typing import Any

from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.services.game import get_game
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def get_org(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    **_,
):
    player = await identity.get_required_player()
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    game_id = data["game_id"]
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
