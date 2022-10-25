from datetime import datetime

from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Context
from aiogram_dialog.widgets.common import Whenable

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums import GameStatus
from shvatka.services import game
from shvatka.services.game import get_authors_games
from shvatka.utils.datetime_utils import tz_game


async def get_my_games(dao: HolderDao, player: dto.Player, **_) -> dict[str, list[dto.Game]]:
    return {"games": await get_authors_games(player, dao.game)}


async def get_game(dao: HolderDao, player: dto.Player, aiogd_context: Context, **_):
    data = aiogd_context.dialog_data
    return {"game": await game.get_game(data["my_game_id"], player, dao.game)}


def not_getting_waivers(data: dict, widget: Whenable, manager: DialogManager):
    return data["game"].status in (GameStatus.underconstruction, GameStatus.ready)


def is_getting_waivers(data: dict, widget: Whenable, manager: DialogManager):
    return data["game"].status == GameStatus.getting_waivers


async def get_game_time(dao: HolderDao, player: dto.Player, aiogd_context: Context, **kwargs):
    result = await get_game(dao, player, aiogd_context, **kwargs)
    time_ = aiogd_context.dialog_data.get("scheduled_time", None)
    result.update(scheduled_time=time_, has_time=time_ is not None)
    return result


async def get_game_datetime(dao: HolderDao, player: dto.Player, aiogd_context: Context, **kwargs):
    result = await get_game(dao, player, aiogd_context, **kwargs)
    date_ = aiogd_context.dialog_data.get("scheduled_date", None)
    time_ = aiogd_context.dialog_data.get("scheduled_time", None)
    result["scheduled_datetime"] = datetime.combine(date_, time_, tzinfo=tz_game)
    return result
