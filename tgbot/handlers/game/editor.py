import logging

import yaml
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram_dialog import StartMode, DialogManager
from dataclass_factory import Factory

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import upsert_game
from shvatka.utils.exceptions import ScenarioNotCorrect
from tgbot.filters.can_be_author import can_be_author
from tgbot.filters.game_status import GameStatusFilter
from tgbot.states import MyGamesPanel
from tgbot.views.commands import MY_GAMES_COMMAND

logger = logging.getLogger(__name__)


async def cmd_save_game(m: Message, dao: HolderDao, dcf: Factory, bot: Bot, player: dto.Player):
    """TODO refactor it =)"""
    document = await bot.download(m.document.file_id)
    try:
        await upsert_game(yaml.safe_load(document), player, dao.game_upserter, dcf)
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
