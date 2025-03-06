from collections import defaultdict
from datetime import datetime

from aiogram_dialog import DialogManager

from shvatka.core.models import dto
from shvatka.core.services.game_stat import get_game_spy
from shvatka.core.services.organizers import get_by_player
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao


async def get_org(
    dao: HolderDao, player: dto.Player, game: dto.Game, dialog_manager: DialogManager, **_
):
    if dialog_manager.middleware_data.get("org", None) is not None:
        org = dialog_manager.middleware_data["org"]
    else:
        org = await get_by_player(player=player, game=game, dao=dao.organizer)
    return {
        "game": game,
        "player": player,
        "org": org,
    }


async def get_spy(
    dao: HolderDao, player: dto.Player, game: dto.Game, dialog_manager: DialogManager, **_
):
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
