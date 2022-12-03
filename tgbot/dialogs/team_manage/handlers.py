from typing import Any

from aiogram.types import Message
from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import get_my_team, get_team_player
from shvatka.services.team import rename_team


async def rename_team_handler(m: Message, widget: Any, dialog_manager: DialogManager, new_name: str):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_team_player(player=player, team=team, dao=dao.team_player)
    await rename_team(team=team, captain=team_player, new_name=new_name, dao=dao.team)
