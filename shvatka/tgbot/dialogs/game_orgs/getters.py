from typing import Any
from aiogram_dialog import DialogManager

from shvatka.core.services import organizers
from shvatka.core.services.game import get_game
from shvatka.core.services.organizers import get_org_by_id
from shvatka.core.views.texts import PERMISSION_EMOJI
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.core.interfaces.identity import IdentityProvider
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from shvatka.tgbot import keyboards as kb


@inject
async def get_orgs(
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
    **_,
):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    game_id = data["game_id"]
    completed = data.get("completed", False)
    author = await identity.get_required_player()
    game = await get_game(
        id_=game_id,
        author=author if not completed else None,
        dao=dao.game,
    )
    orgs = await organizers.get_secondary_orgs(game, dao.organizer, with_deleted=True)
    inline_query = kb.AddGameOrgID(
        game_manage_token=game.manage_token,
        game_id=game.id,
    )
    return {
        "game": game,
        "orgs": orgs,
        "inline_query": inline_query.pack(),
    }


@inject
async def get_org(dialog_manager: DialogManager, dao: FromDishka[HolderDao], **_):
    org_id = dialog_manager.dialog_data["org_id"]
    org = await get_org_by_id(org_id, dao.organizer)
    return {
        "org": org,
        "can_spy": PERMISSION_EMOJI[org.can_spy],
        "can_see_log_keys": PERMISSION_EMOJI[org.can_see_log_keys],
        "can_validate_waivers": PERMISSION_EMOJI[org.can_validate_waivers],
        "view_scenario": PERMISSION_EMOJI[org.view_scenario],
    }
