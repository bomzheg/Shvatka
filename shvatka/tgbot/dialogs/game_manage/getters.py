import logging
from datetime import date, datetime, time, timedelta
from typing import Any

from aiogram import Bot
from aiogram_dialog import DialogManager
from dishka import AsyncContainer, FromDishka
from dishka.integrations.aiogram import CONTAINER_NAME
from dishka.integrations.aiogram_dialog import inject
from telegraph.aio import Telegraph

from shvatka.common.config.models.main import FeaturesConfig
from shvatka.common.url_factory import UrlFactory
from shvatka.core.interfaces.dal.complex import TypedKeyGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.season.interactors import FindSlotsNearGameStartInteractor
from shvatka.core.services import game
from shvatka.core.services.game import get_authors_games, get_completed_games
from shvatka.core.utils.datetime_utils import DATE_FORMAT, tz_game
from shvatka.core.waiver.services import get_all_played
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.keys import get_or_create_keys_page

logger = logging.getLogger(__name__)


@inject
async def get_my_games(
    dao: FromDishka[HolderDao], identity: FromDishka[IdentityProvider], **_
) -> dict[str, list[dto.Game]]:
    return {"games": await get_authors_games(identity, dao.game)}


@inject
async def get_games(dao: FromDishka[HolderDao], **_) -> dict[str, list[dto.Game]]:
    return {"games": await get_completed_games(dao.game)}


@inject
async def get_completed_game(dao: FromDishka[HolderDao], dialog_manager: DialogManager, **_):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    game_id = dialog_manager.dialog_data.get("game_id", None) or data["game_id"]
    dishka: AsyncContainer = dialog_manager.middleware_data[CONTAINER_NAME]
    url_factory = await dishka.get(UrlFactory)
    return {
        "game": await game.get_game(
            id_=game_id,
            dao=dao.game,
        ),
        "webapp_url": url_factory.get_game_id_web_url(game_id),
    }


@inject
async def get_game_waivers(dao: FromDishka[HolderDao], dialog_manager: DialogManager, **_):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    game_id = dialog_manager.dialog_data.get("game_id", None) or data["game_id"]
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
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    telegraph: FromDishka[Telegraph],
    identity: FromDishka[IdentityProvider],
    typed_keys: FromDishka[TypedKeyGetter],
    **_,
):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    game_id = dialog_manager.dialog_data.get("game_id", None) or data["game_id"]
    current_game = await game.get_game(
        id_=game_id,
        dao=dao.game,
    )
    return {
        "game": current_game,
        "key_link": await get_or_create_keys_page(
            game=current_game,
            telegraph=telegraph,
            dao=dao,
            typed_keys=typed_keys,
            identity=identity,
        ),
    }


@inject
async def get_game_results(
    dialog_manager: DialogManager,
    dao: FromDishka[HolderDao],
    **_,
):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    game_id = dialog_manager.dialog_data.get("game_id", None) or data["game_id"]
    return {
        "game": await game.get_game(
            id_=game_id,
            dao=dao.game,
        ),
    }


async def _my_game(
    dao: HolderDao, player: dto.Player, dialog_manager: DialogManager
) -> dict[str, Any]:
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    game_id = dialog_manager.dialog_data.get("my_game_id", None) or data["my_game_id"]
    return {
        "game": await game.get_preview_game(
            id_=game_id,
            author=player,
            dao=dao.game,
        )
    }


@inject
async def get_game(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    features: FromDishka[FeaturesConfig],
    **_,
) -> dict[str, Any]:
    return dict(
        features=features,
        **await _my_game(dao, await identity.get_required_player(), dialog_manager),
    )


@inject
async def get_game_with_channel(
    dao: FromDishka[HolderDao], dialog_manager: DialogManager, bot: Bot, **_
):
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


@inject
async def get_game_time(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    **_,
):
    result = await _my_game(dao, await identity.get_required_player(), dialog_manager)
    time_: str | None = dialog_manager.dialog_data.get("scheduled_time", None)
    result.update(scheduled_time=time_, has_time=time_ is not None)
    return result


@inject
async def get_game_datetime(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    **_,
):
    result = await _my_game(dao, await identity.get_required_player(), dialog_manager)
    result["scheduled_datetime"] = _scheduled_at(dialog_manager)
    return result


SEASON_WIDE_WINDOW = timedelta(days=366)
"""The whole season, for «перенести ближайшую дату сюда»."""

NEAREST_SLOTS = 2
"""One date before and one after is a choice; a list of nine is a search."""


@inject
async def get_slots_near_game(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    suggester: FromDishka[FindSlotsNearGameStartInteractor],
    **_,
):
    result = await _my_game(dao, await identity.get_required_player(), dialog_manager)
    at = _scheduled_at(dialog_manager)
    slots = await suggester(at, identity)
    result.update(
        scheduled_datetime=at,
        scheduled_day=at.astimezone(tz_game).date(),
        scheduled_day_text=at.astimezone(tz_game).strftime(DATE_FORMAT),
        slots=slots,
        nearest=slots[0] if slots else None,
    )
    return result


@inject
async def get_no_slot_near_game(
    dao: FromDishka[HolderDao],
    dialog_manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    suggester: FromDishka[FindSlotsNearGameStartInteractor],
    **_,
):
    result = await _my_game(dao, await identity.get_required_player(), dialog_manager)
    at = _scheduled_at(dialog_manager)
    # nothing is within ±3 days, so the offer widens to the whole season
    nearest = (await suggester(at, identity, SEASON_WIDE_WINDOW))[:NEAREST_SLOTS]
    result.update(
        scheduled_datetime=at,
        scheduled_day=at.astimezone(tz_game).date(),
        scheduled_day_text=at.astimezone(tz_game).strftime(DATE_FORMAT),
        slots=nearest,
        has_slots=bool(nearest),
    )
    return result


def _scheduled_at(dialog_manager: DialogManager) -> datetime:
    return datetime.combine(
        date=date.fromisoformat(dialog_manager.dialog_data["scheduled_date"]),
        time=time.fromisoformat(dialog_manager.dialog_data["scheduled_time"]),
        tzinfo=tz_game,
    )
