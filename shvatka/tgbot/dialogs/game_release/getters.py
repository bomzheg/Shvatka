from typing import Any

from adaptix import Retort
from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.games.release_interactors import GetGameReleaseInteractor
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models.dto import hints
from shvatka.core.models.enums import GameStatus
from shvatka.core.services.game import get_game
from shvatka.infrastructure.db.dao.holder import HolderDao

EARLY_ENOUGH = (
    GameStatus.underconstruction,
    GameStatus.ready,
    GameStatus.getting_waivers,
)
"""Statuses in which a release still has an audience to be announced to."""


@inject
async def get_release(
    dialog_manager: DialogManager,
    dao: FromDishka[HolderDao],
    idp: FromDishka[IdentityProvider],
    interactor: FromDishka[GetGameReleaseInteractor],
    **_,
):
    data: dict[str, Any] = dialog_manager.start_data  # type: ignore[assignment]
    game_id = int(data["game_id"])
    game = await get_game(id_=game_id, author=await idp.get_required_player(), dao=dao.game)
    release = await interactor(game_id=game_id)
    is_published = release is not None and release.is_published
    return {
        "game": game,
        "hints": release.hints if release else [],
        "has_release": release is not None,
        "is_published": is_published,
        # a release written before the waivers start waits for them; one written
        # after the game started stays on the site only
        "waits_for_waivers": not is_published
        and game.status in (GameStatus.underconstruction, GameStatus.ready),
        "late": not is_published and game.status not in EARLY_ENOUGH,
    }


async def get_composed_hints(dialog_manager: DialogManager, **_):
    retort: Retort = dialog_manager.middleware_data["retort"]
    hints_ = retort.load(dialog_manager.dialog_data.get("hints", []), list[hints.AnyHint])
    return {
        "hints": hints_,
        "has_hints": len(hints_) > 0,
    }
