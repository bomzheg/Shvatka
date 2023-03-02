from typing import Any

from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from infrastructure.db.dao.holder import HolderDao
from shvatka.models import dto, enums
from shvatka.services.player import (
    get_my_team,
    get_full_team_player,
    flip_permission,
    get_team_player_by_player,
    get_player_by_id,
    leave,
    change_role,
    change_emoji,
)
from shvatka.services.team import rename_team, change_team_desc
from tgbot import states


async def rename_team_handler(
    m: Message, widget: Any, dialog_manager: DialogManager, new_name: str
):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    await rename_team(team=team, captain=team_player, new_name=new_name, dao=dao.team)


async def change_desc_team_handler(
    m: Message, widget: Any, dialog_manager: DialogManager, new_desc: str
):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
    await change_team_desc(team=team, captain=team_player, new_desc=new_desc, dao=dao.team)


async def select_player(c: CallbackQuery, widget: Any, manager: DialogManager, player_id: str):
    data = manager.dialog_data
    data["selected_player_id"] = int(player_id)
    await manager.switch_to(states.CaptainsBridgeSG.player)


async def change_permission_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    team = await get_my_team(captain, dao.team_player)
    captain_team_player = await get_full_team_player(captain, team, dao.team_player)
    player_id = manager.dialog_data["selected_player_id"]
    player = await get_player_by_id(player_id, dao.player)
    team_player = await get_team_player_by_player(player, dao.team_player)
    permission = enums.TeamPlayerPermission[button.widget_id]
    await flip_permission(captain_team_player, team_player, permission, dao.team_player)


async def remove_player_handler(c: CallbackQuery, button: Button, manager: DialogManager):
    await c.answer()
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    player_id = manager.dialog_data["selected_player_id"]
    player = await get_player_by_id(player_id, dao.player)
    await leave(player=player, remover=captain, dao=dao.team_leaver)
    bot: Bot = manager.middleware_data["bot"]
    team = await get_my_team(captain, dao.team_player)
    await bot.send_message(
        chat_id=team.get_chat_id(),
        text=f"Игрок {hd.quote(player.name_mention)} был исключён из команды.",
    )
    await manager.switch_to(state=states.CaptainsBridgeSG.players)


async def change_role_handler(m: Message, widget: Any, manager: DialogManager, role: str):
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    player_id = manager.dialog_data["selected_player_id"]
    player = await get_player_by_id(player_id, dao.player)
    team = await get_my_team(captain, dao.team_player)
    await change_role(player, team, captain, role, dao.team_player)
    await manager.switch_to(states.CaptainsBridgeSG.player)


async def change_emoji_handler(m: Message, widget: Any, manager: DialogManager, emoji: str):
    dao: HolderDao = manager.middleware_data["dao"]
    captain: dto.Player = manager.middleware_data["player"]
    player_id = manager.dialog_data["selected_player_id"]
    player = await get_player_by_id(player_id, dao.player)
    team = await get_my_team(captain, dao.team_player)
    await change_emoji(player, team, captain, emoji, dao.team_player)
    await manager.switch_to(states.CaptainsBridgeSG.player)
