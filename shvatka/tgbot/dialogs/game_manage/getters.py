import logging
from datetime import datetime, time, date
from typing import Any

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from dishka import AsyncContainer, FromDishka
from dishka.integrations.aiogram import CONTAINER_NAME
from dishka.integrations.aiogram_dialog import inject
from telegraph import Telegraph

from shvatka.common.url_factory import UrlFactory
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services import game
from shvatka.core.services.game import get_authors_games, get_completed_games
from shvatka.core.services.waiver import get_all_played
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture import ResultsPainter
from shvatka.tgbot.views.keys import get_or_create_keys_page

logger = logging.getLogger(__name__)


@inject
async def get_my_games(
    dao: HolderDao, identity: FromDishka[IdentityProvider], **_
) -> dict[str, list[dto.Game]]:
    return {"games": await get_authors_games(identity, dao.game)}


async def get_games(dao: HolderDao, **_) -> dict[str, list[dto.Game]]:
    return {"games": await get_completed_games(dao.game)}


async def get_completed_game(dao: HolderDao, dialog_manager: DialogManager, **_):
    game_id = (
        dialog_manager.dialog_data.get("game_id", None) or dialog_manager.start_data["game_id"]
    )
    dishka: AsyncContainer = dialog_manager.middleware_data[CONTAINER_NAME]
    url_factory = await dishka.get(UrlFactory)
    return {
        "game": await game.get_game(
            id_=game_id,
            dao=dao.game,
        ),
        "webapp_url": url_factory.get_game_id_web_url(game_id),
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


@inject
async def get_game_keys(
    dao: HolderDao,
    dialog_manager: DialogManager,
    telegraph: FromDishka[Telegraph],
    identity: FromDishka[IdentityProvider],
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
        "key_link": await get_or_create_keys_page(
            game=current_game, telegraph=telegraph, dao=dao, identity=identity
        ),
    }


@inject
async def get_game_results(
    dialog_manager: DialogManager,
    dao: HolderDao,
    identity: FromDishka[IdentityProvider],
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
    file_id = await results_painter.get_game_results(current_game, identity=identity)
    return {
        "game": current_game,
        "results.png": MediaAttachment(file_id=MediaId(file_id=file_id), type=ContentType.PHOTO),
    }


async def get_game(
    dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **_
) -> dict[str, Any]:
    game_id = (
        dialog_manager.dialog_data.get("my_game_id", None)
        or dialog_manager.start_data["my_game_id"]
    )
    return {
        "game": await game.get_preview_game(
            id_=game_id,
            author=player,
            dao=dao.game,
        )
    }


async def get_game_with_channel(dao: HolderDao, dialog_manager: DialogManager, bot: Bot, **_):
    game_id: int | None = dialog_manager.dialog_data.get("game_id", None)
    if game_id is None:
        logger.warning("game_id is None")
        return {"invite": "sorry something happened", "game": None}
    game_ = await game.get_game(id_=game_id, dao=dao.game)
    if game_.results.published_chanel_id is None:
        logger.warning("published chanel id is None")
        return {"invite": "sorry something happened", "game": game_}
    chat = await bot.get_chat(game_.results.published_chanel_id)
    return {
        "game": game_,
        "invite": chat.invite_link,
    }


async def get_game_time(
    dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **kwargs
):
    result = await get_game(dao, player, dialog_manager, **kwargs)
    time_: str | None = dialog_manager.dialog_data.get("scheduled_time", None)
    result.update(scheduled_time=time_, has_time=time_ is not None)
    return result


async def get_game_datetime(
    dao: HolderDao, player: dto.Player, dialog_manager: DialogManager, **kwargs
):
    result = await get_game(dao, player, dialog_manager, **kwargs)
    date_: str = dialog_manager.dialog_data["scheduled_date"]
    time_: str = dialog_manager.dialog_data["scheduled_time"]
    result["scheduled_datetime"] = datetime.combine(
        date=date.fromisoformat(date_),
        time=time.fromisoformat(time_),
        tzinfo=tz_game,
    )
    return result
