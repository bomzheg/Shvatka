import typing
from typing import Any

from aiogram.types import CallbackQuery
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager

from shvatka.core.services.team import get_team_by_id, get_team_by_forum_team_id
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
