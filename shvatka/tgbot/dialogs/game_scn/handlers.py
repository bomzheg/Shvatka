import logging
import typing
from typing import Any, BinaryIO

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, ManagedMultiselect
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.games.editor_interactors import ImportGameZipInteractor
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import enums
from shvatka.core.services.achievement import add_achievement
from shvatka.core.services.game import (
    add_level,
    check_new_game_name_available,
    create_game,
    get_full_game,
)
from shvatka.core.services.level import get_all_my_free_levels, get_by_id
from shvatka.core.utils.exceptions import FilesCantBeSentToTg, ScenarioNotCorrect
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states

logger = logging.getLogger(__name__)


@inject
async def process_name(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
):
    author = await identity.get_required_player()
    game_name: str = typing.cast(str, m.text)
    if game_name.lower().strip() == "мудро":
        await add_achievement(
            player=author, name=enums.Achievement.game_name_joke, dao=dao.achievement
        )
        return await m.answer(
            "Лол, я ждал эту шутку. " "Но нет, игра не может называться {name}".format(
                name=hd.bold(hd.quote(game_name))
            )
        )
    await check_new_game_name_available(name=game_name.strip(), author=author, dao=dao.game)
    data = manager.dialog_data
    if not isinstance(data, dict):
        data = {}
    data["game_name"] = m.text
    await manager.next()
    return None


@inject
async def process_zip_scn(
    m: Message,
    dialog_: Any,
    manager: DialogManager,
    interactor: FromDishka[ImportGameZipInteractor],
    identity: FromDishka[IdentityProvider],
) -> None:
    player = await identity.get_required_player()
    bot: Bot = manager.middleware_data["bot"]
    assert m.document
    document: BinaryIO = await bot.download(m.document.file_id)  # type: ignore[assignment]
    try:
        # the bot has always rewritten the author's game of that name, and its
        # dialog has nowhere to ask — the web is where the question is put
        game = await interactor(zip_file=document, identity=identity, overwrite=True)
    except ScenarioNotCorrect as e:
        await m.reply(f"Ошибка {e}\n попробуйте исправить файл")
        logger.exception("game scenario from player %s has problems", player.id, exc_info=e)
        return
    except FilesCantBeSentToTg as e:
        await m.reply(render_tg_rejections(e))
        logger.warning(
            "telegram refused %s files of the scenario from player %s",
            len(e.errors),
            player.id,
            exc_info=e,
        )
        return
    await m.reply("Успешно сохранено")
    await manager.done(result={"game": game})


def render_tg_rejections(error: FilesCantBeSentToTg) -> str:
    problems = "\n".join(f"• {hd.quote(str(e.notify_user))}" for e in error.errors)
    return (
        "Telegram не принял часть файлов, игра не сохранена:\n"
        f"{problems}\n\n"
        "Исправьте эти файлы и загрузите zip заново."
    )


@inject
async def save_game(
    c: CallbackQuery,
    button: Button,
    manager: DialogManager,
    identity: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
):
    author = await identity.get_required_player()
    name: str = manager.dialog_data["game_name"]
    levels = await get_all_my_free_levels(author, dao.level)
    multiselect = typing.cast(ManagedMultiselect, manager.find("my_free_level_ids"))
    levels = list(filter(lambda level: multiselect.is_checked(level.db_id), levels))
    game = await create_game(author=author, name=name, dao=dao.game_creator, levels=levels)
    assert isinstance(c.message, Message)
    await c.message.edit_text("Игра успешно сохранена")
    await manager.done(result={"game": game})


async def edit_level(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    await manager.start(states.LevelManageSG.menu, data={"level_id": int(item_id)})


@inject
async def add_level_handler(
    c: CallbackQuery,
    button: Any,
    manager: DialogManager,
    item_id: str,
    idp: FromDishka[IdentityProvider],
    dao: FromDishka[HolderDao],
):
    data: dict[str, Any] = manager.start_data  # type: ignore[assignment]
    game_id = data["game_id"]
    author = await idp.get_required_player()
    game = await get_full_game(game_id, identity=idp, dao=dao.game)
    level = await get_by_id(int(item_id), author=author, dao=dao.level)
    await add_level(game=game, level=level, author=author, dao=dao.game_creator)
    await manager.switch_to(state=states.GameEditSG.current_levels)
