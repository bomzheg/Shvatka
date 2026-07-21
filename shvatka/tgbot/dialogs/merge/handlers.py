import urllib.parse
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.notifications.request_interactors import (
    CreatePlayerMergeRequestInteractor,
    CreateTeamMergeRequestInteractor,
)
from shvatka.core.services.team import get_team_by_forum_team_id
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states


async def select_forum_team(
    c: CallbackQuery, widget: Any, manager: DialogManager, forum_team_id: str
):
    manager.dialog_data["forum_team_id"] = int(forum_team_id)
    await manager.switch_to(states.MergeTeamsSG.confirm)


@inject
async def confirm_merge(
    c: CallbackQuery,
    button: Any,
    manager: DialogManager,
    dao: FromDishka[HolderDao],
    identity: FromDishka[IdentityProvider],
    interactor: FromDishka[CreateTeamMergeRequestInteractor],
):
    start_data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    secondary = await get_team_by_forum_team_id(manager.dialog_data["forum_team_id"], dao.team)
    await interactor(
        identity=identity,
        primary_team_id=start_data["team_id"],
        secondary_team_id=secondary.id,
    )
    await c.answer("Заявка на объединение отправлена", show_alert=True)
    await manager.done()


@inject
async def player_link_handler(
    m: Message, widget: Any, manager: DialogManager, dao: FromDishka[HolderDao]
):
    url = urllib.parse.urlparse(m.text)
    assert isinstance(url.query, str)
    forum_id = int(urllib.parse.parse_qs(url.query)["showuser"][0])
    forum_user = await dao.forum_user.get_by_forum_id(forum_id)
    manager.dialog_data["forum_player_id"] = forum_user.db_id
    await manager.switch_to(states.MergePlayersSG.confirm)


@inject
async def confirm_merge_player(
    c: CallbackQuery,
    button: Any,
    manager: DialogManager,
    dao: FromDishka[HolderDao],
    identity: FromDishka[IdentityProvider],
    interactor: FromDishka[CreatePlayerMergeRequestInteractor],
):
    secondary_forum = await dao.forum_user.get_by_id(manager.dialog_data["forum_player_id"])
    await interactor(identity=identity, secondary_player_id=secondary_forum.player_id)
    await c.answer("Заявка на объединение отправлена", show_alert=True)
    await manager.done()
