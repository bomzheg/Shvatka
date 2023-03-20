from datetime import datetime, time, date

from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from telegraph import Telegraph

from shvatka.core.models import dto
from shvatka.core.services import game
from shvatka.core.services.game import get_authors_games, get_completed_games
from shvatka.core.services.waiver import get_all_played
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture import ResultsPainter
from shvatka.tgbot.views.keys import get_or_create_keys_page


async def get_my_games(dao: HolderDao, player: dto.Player, **_) -> dict[str, list[dto.Game]]:
    return {"games": await get_authors_games(player, dao.game)}


async def get_games(dao: HolderDao, **_) -> dict[str, list[dto.Game]]:
    return {"games": await get_completed_games(dao.game)}


async def get_completed_game(dao: HolderDao, dialog_manager: DialogManager, **_):
    game_id = (
        dialog_manager.dialog_data.get("game_id", None) or dialog_manager.start_data["game_id"]
    )
    return {
        "game": await game.get_game(
            id_=game_id,
            dao=dao.game,
        )
    }


async def get_game_waivers(dao: HolderDao, dialog_manager: DialogManager, **_):
    game_id = (
        dialog_manager.dialog_data.get("game_id", None) or dialog_manager.start_data["game_id"]
    )
    current_game = await game.get_game(
        id_=game_id,
        dao=dao.game,
    )
    return {
        "game": current_game,
        "waivers": await get_all_played(current_game, dao.waiver),
    }


async def get_game_keys(
    dao: HolderDao,
    dialog_manager: DialogManager,
    player: dto.Player,
    telegraph: Telegraph,
    **_,
):
    game_id = (
        dialog_manager.dialog_data.get("game_id", None) or dialog_manager.start_data["game_id"]
    )
    current_game = await game.get_game(
        id_=game_id,
        dao=dao.game,
    )
    return {
        "game": current_game,
        "key_link": await get_or_create_keys_page(current_game, player, telegraph, dao),
    }


async def get_game_results(
    dao: HolderDao,
    dialog_manager: DialogManager,
    player: dto.Player,
    results_painter: ResultsPainter,
    **_,
):
    game_id = (
        dialog_manager.dialog_data.get("game_id", None) or dialog_manager.start_data["game_id"]
    )
    current_game = await game.get_game(
        id_=game_id,
        dao=dao.game,
    )
    file_id = await results_painter.get_game_results(current_game, player)
    return {
        "game": current_game,
        "results.png": MediaAttachment(file_id=MediaId(file_id=file_id), type=ContentType.PHOTO),
    }


async def get_game(dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **_):
    game_id = (
        dialog_manager.dialog_data.get("my_game_id", None)
        or dialog_manager.start_data["my_game_id"]
    )
    return {
        "game": await game.get_game(
            id_=game_id,
            author=player,
            dao=dao.game,
        )
    }


async def get_game_time(
    dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **kwargs
):
    result = await get_game(dao, player, dialog_manager, **kwargs)
    time_ = dialog_manager.dialog_data.get("scheduled_time", None)
    result.update(scheduled_time=time_, has_time=time_ is not None)
    return result


async def get_game_datetime(
    dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **kwargs
):
    result = await get_game(dao, player, dialog_manager, **kwargs)
    date_ = dialog_manager.dialog_data.get("scheduled_date", None)
    time_ = dialog_manager.dialog_data.get("scheduled_time", None)
    result["scheduled_datetime"] = datetime.combine(
        date=date.fromisoformat(date_),
        time=time.fromisoformat(time_),
        tzinfo=tz_game,
    )
    return result
