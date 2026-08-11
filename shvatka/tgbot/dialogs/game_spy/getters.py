from collections import defaultdict
from datetime import datetime

from aiogram_dialog import DialogManager

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.identity import IdentityProvider
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from shvatka.core.services.game_stat import get_game_spy
from shvatka.core.services.organizers import get_by_player
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao


@inject
async def get_org(
    dao: HolderDao,
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    current_game: FromDishka[CurrentGameProvider],
    **_,
):
    game = await current_game.get_required_game()
    player = await identity.get_required_player()
    if dialog_manager.middleware_data.get("org", None) is not None:
        org = dialog_manager.middleware_data["org"]
    else:
        org = await get_by_player(player=player, game=game, dao=dao.organizer)
    return {
        "game": game,
        "player": player,
        "org": org,
    }


@inject
async def get_spy(
    dao: HolderDao,
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    current_game: FromDishka[CurrentGameProvider],
    **_,
):
    game = await current_game.get_required_game()
    player = await identity.get_required_player()
    stat = sorted(
        await get_game_spy(game, player, dao.game_stat),
        key=lambda x: (-x.level_number, x.start_at),
    )
    result = defaultdict(list)
    finished = []
    for s in stat:
        if s.is_finished:
            finished.append(s)
        else:
            result[s.level_number].append(s)
    return {
        "stat": result,
        "finished": finished,
        "now": datetime.now(tz=tz_utc),
    }


async def get_keys(dialog_manager: DialogManager, **_):
    date_iso = dialog_manager.dialog_data.get("updated", None)
    if date_iso is not None:
        updated = datetime.fromisoformat(date_iso)
    else:
        updated = None
    return {
        "key_link": dialog_manager.dialog_data.get("key_link", None),
        "updated": updated,
    }
