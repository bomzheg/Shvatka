import logging
from zipfile import Path as ZipPath

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram_dialog import StartMode, DialogManager
from dataclass_factory import Factory

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.services.game import upsert_game
from shvatka.utils.exceptions import ScenarioNotCorrect
from tgbot.filters.can_be_author import can_be_author
from tgbot.filters.game_status import GameStatusFilter
from tgbot.services.scenario import unpack_scn
from tgbot.states import MyGamesPanel
from tgbot.views.commands import MY_GAMES_COMMAND

logger = logging.getLogger(__name__)


async def cmd_save_game(
    m: Message, dao: HolderDao, dcf: Factory, bot: Bot, player: dto.Player, file_storage: FileStorage,
):
    """TODO refactor it =)"""
    document = await bot.download(m.document.file_id)
    try:
        with unpack_scn(ZipPath(document)).open() as scn:
            await upsert_game(scn, player, dao.game_upserter, dcf, file_storage)
    except ScenarioNotCorrect as e:
        await m.reply(f"Ошибка {e}\n попробуйте исправить файл")
        logger.error("game scenario from player %s has problems", player.id, exc_info=e)
        return
    await m.reply("Успешно сохранено")


async def get_manage(_: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MyGamesPanel.choose_game, mode=StartMode.RESET_STACK)


def setup() -> Router:
    router = Router(name=__name__)
    router.message.filter(
        GameStatusFilter(running=False),
        can_be_author,
    )

    router.message.register(cmd_save_game, F.content_type == ContentType.DOCUMENT)
    # TODO refactor it filters^ (state?)
    router.message.register(get_manage, Command(commands=MY_GAMES_COMMAND))
    return router
