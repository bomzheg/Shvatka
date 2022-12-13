from datetime import datetime, time, date

from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services import game
from shvatka.services.game import get_authors_games, get_completed_games
from shvatka.utils.datetime_utils import tz_game


async def get_my_games(dao: HolderDao, player: dto.Player, **_) -> dict[str, list[dto.Game]]:
    return {"games": await get_authors_games(player, dao.game)}


async def get_games(dao: HolderDao, **_) -> dict[str, list[dto.Game]]:
    return {"games": await get_completed_games(dao.game)}


async def get_completed_game(dao: HolderDao, dialog_manager: DialogManager, **_):
    game_id = dialog_manager.dialog_data.get("game_id", None) or dialog_manager.start_data["game_id"]
    return {"game": await game.get_game(
        id_=game_id,
        dao=dao.game,
    )}


async def get_game(dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **_):
    game_id = dialog_manager.dialog_data.get("my_game_id", None) or dialog_manager.start_data["my_game_id"]
    return {"game": await game.get_game(
        id_=game_id,
        author=player,
        dao=dao.game,
    )}


async def get_game_time(dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **kwargs):
    result = await get_game(dao, player, dialog_manager, **kwargs)
    time_ = dialog_manager.dialog_data.get("scheduled_time", None)
    result.update(scheduled_time=time_, has_time=time_ is not None)
    return result


async def get_game_datetime(dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **kwargs):
    result = await get_game(dao, player, dialog_manager, **kwargs)
    date_ = dialog_manager.dialog_data.get("scheduled_date", None)
    time_ = dialog_manager.dialog_data.get("scheduled_time", None)
    result["scheduled_datetime"] = datetime.combine(
        date=date.fromisoformat(date_), time=time.fromisoformat(time_), tzinfo=tz_game,
    )
    return result
