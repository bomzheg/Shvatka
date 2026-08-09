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
    return {
        "game": game,
        "banner": release.banner if release else None,
        "hints": release.hints if release else [],
        "has_release": release is not None,
        # where a release stands is the announcing view's business, so what it
        # is doing now is read off the game's status instead
        "in_channel": game.status == GameStatus.getting_waivers,
        # a release written before the waivers start waits for them; one written
        # after the game started stays on the site only
        "waits_for_waivers": game.status in (GameStatus.underconstruction, GameStatus.ready),
        "late": game.status not in EARLY_ENOUGH,
    }


async def get_composed_release(dialog_manager: DialogManager, **_):
    retort: Retort = dialog_manager.middleware_data["retort"]
    dumped_banner = dialog_manager.dialog_data.get("banner")
    banner = retort.load(dumped_banner, hints.PhotoHint) if dumped_banner else None
    hints_ = retort.load(dialog_manager.dialog_data.get("hints", []), list[hints.AnyHint])
    return {
        "banner": banner,
        "has_banner": banner is not None,
        "hints": hints_,
        "has_hints": len(hints_) > 0,
        "is_empty": banner is None and not hints_,
    }
