from typing import Any

from adaptix import Retort
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.games.release_interactors import (
    DeleteGameReleaseInteractor,
    GetGameReleaseInteractor,
    SaveGameReleaseInteractor,
)
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models.dto import hints
from shvatka.tgbot import states
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.hint_sender import HintSender


def _game_id(manager: DialogManager) -> int:
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    return int(data["game_id"])


def _composed(manager: DialogManager) -> list[dict[str, Any]]:
    return manager.dialog_data.setdefault("hints", [])


def load_banner(manager: DialogManager, retort: Retort) -> hints.PhotoHint | None:
    dumped = manager.dialog_data.get("banner")
    return retort.load(dumped, hints.PhotoHint) if dumped else None


def load_composed(manager: DialogManager, retort: Retort) -> list[hints.AnyHint]:
    return retort.load(_composed(manager), list[hints.AnyHint])


@inject
async def to_compose_release(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
    interactor: FromDishka[GetGameReleaseInteractor],
):
    release = await interactor(game_id=_game_id(manager))
    manager.dialog_data["banner"] = (
        retort.dump(release.banner, hints.PhotoHint) if release and release.banner else None
    )
    manager.dialog_data["hints"] = (
        retort.dump(release.hints, list[hints.AnyHint]) if release else []
    )
    await manager.switch_to(states.GameReleaseSG.banner)


@inject
async def process_banner(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    retort: FromDishka[Retort],
    parser: FromDishka[HintParser],
    idp: FromDishka[IdentityProvider],
) -> None:
    hint = await parser.parse(m, await idp.get_required_player())
    if not isinstance(hint, hints.PhotoHint):
        await m.reply("Баннер — это картинка (можно с подписью). Пришли фото.")
        return
    manager.dialog_data["banner"] = retort.dump(hint, hints.PhotoHint)
    await manager.switch_to(states.GameReleaseSG.compose)


async def drop_banner(c: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["banner"] = None
    await c.answer("Баннер убран")


@inject
async def process_release_message(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    retort: FromDishka[Retort],
    parser: FromDishka[HintParser],
    idp: FromDishka[IdentityProvider],
) -> None:
    hint = await parser.parse(m, await idp.get_required_player())
    _composed(manager).append(retort.dump(hint))


async def reset_composed_release(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    manager.dialog_data["hints"] = []


@inject
async def preview_release(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
    hint_sender: FromDishka[HintSender],
):
    banner = load_banner(manager, retort)
    composed = load_composed(manager, retort)
    assert c.message is not None
    for hint in [banner, *composed] if banner else composed:
        await hint_sender.send_hint(hint, c.message.chat.id)
    await manager.switch_to(states.GameReleaseSG.confirm)


@inject
async def save_release(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    retort: FromDishka[Retort],
    idp: FromDishka[IdentityProvider],
    interactor: FromDishka[SaveGameReleaseInteractor],
):
    banner = load_banner(manager, retort)
    composed = load_composed(manager, retort)
    if banner is None and not composed:
        await c.answer("Релиз пустой — нечего сохранять", show_alert=True)
        return
    await interactor(game_id=_game_id(manager), banner=banner, hints_=composed, identity=idp)
    manager.dialog_data["banner"] = None
    manager.dialog_data["hints"] = []
    await c.answer("Релиз сохранён")
    await manager.switch_to(states.GameReleaseSG.menu)


@inject
async def show_release(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    interactor: FromDishka[GetGameReleaseInteractor],
    hint_sender: FromDishka[HintSender],
):
    release = await interactor(game_id=_game_id(manager))
    if release is None:
        await c.answer("Релиза пока нет")
        return
    assert c.message is not None
    for hint in release.parts:
        await hint_sender.send_hint(hint, c.message.chat.id)


@inject
async def delete_release(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    idp: FromDishka[IdentityProvider],
    interactor: FromDishka[DeleteGameReleaseInteractor],
):
    await interactor(game_id=_game_id(manager), identity=idp)
    manager.dialog_data["banner"] = None
    manager.dialog_data["hints"] = []
    await c.answer("Релиз удалён")
