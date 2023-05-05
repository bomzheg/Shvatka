import typing
import urllib.parse
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager

from shvatka.core.services.team import get_team_by_id, get_team_by_forum_team_id
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states, keyboards as kb
from shvatka.tgbot.utils.data import MiddlewareData


async def select_forum_team(
    c: CallbackQuery, widget: Any, manager: DialogManager, forum_team_id: str
):
    manager.dialog_data["forum_team_id"] = int(forum_team_id)
    await manager.switch_to(states.MergeTeamsSG.confirm)


async def confirm_merge(c: CallbackQuery, button: Any, manager: DialogManager):
    data = typing.cast(MiddlewareData, manager.middleware_data)
    dao = data["dao"]
    captain = data["player"]
    primary = await get_team_by_id(manager.start_data["team_id"], dao.team)
    secondary = await get_team_by_forum_team_id(manager.dialog_data["forum_team_id"], dao.team)
    await data["bot"].send_message(
        chat_id=data["config"].game_log_chat,
        text=f"Капитан {hd.quote(captain.name_mention)} предлагает объединить "
        f"свою команду {hd.quote(primary.name)} "
        f"с форумной версией {hd.quote(secondary.name)}",
        reply_markup=kb.get_team_merge_confirm_kb(primary, secondary),
    )
    await c.answer("Заявка на объединение отправлена", show_alert=True)
    await manager.done()


async def player_link_handler(m: Message, widget: Any, manager: DialogManager):
    url = urllib.parse.urlparse(m.text)
    assert isinstance(url.query, str)
    forum_id = int(urllib.parse.parse_qs(url.query)["showuser"][0])
    dao: HolderDao = manager.middleware_data["dao"]
    forum_user = await dao.forum_user.get_by_forum_id(forum_id)
    manager.dialog_data["forum_player_id"] = forum_user.db_id
    await manager.switch_to(states.MergePlayersSG.confirm)


async def confirm_merge_player(c: CallbackQuery, button: Any, manager: DialogManager):
    data = typing.cast(MiddlewareData, manager.middleware_data)
    dao = data["dao"]
    primary = data["player"]
    secondary_forum = await dao.forum_user.get_by_id(manager.dialog_data["forum_player_id"])
    secondary = await dao.player.get_by_id(secondary_forum.player_id)
    await data["bot"].send_message(
        chat_id=data["config"].game_log_chat,
        text=f"Игрок {hd.quote(primary.name_mention)} предлагает объединить "
        f"свои достижения "
        f"с форумной версией {hd.quote(secondary.name_mention)}",
        reply_markup=kb.get_player_merge_confirm_kb(primary, secondary),
    )
    await c.answer("Заявка на объединение отправлена", show_alert=True)
    await manager.done()
