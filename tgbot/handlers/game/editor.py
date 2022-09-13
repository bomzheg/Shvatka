import logging

import yaml
from aiogram import Router, Dispatcher, Bot
from aiogram.filters import ContentTypesFilter, Command
from aiogram.types import Message
from aiogram_dialog import StartMode, DialogManager
from dataclass_factory import Factory

from shvatka.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import upsert_game
from shvatka.utils.exceptions import ScenarioNotCorrect
from tgbot.filters.game_status import GameStatusFilter
from tgbot.states import MyGamesPanel

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def cmd_save_game(m: Message, dao: HolderDao, dcf: Factory, bot: Bot, player: dto.Player):
    """TODO refactor it =)"""
    document = await bot.download(m.document.file_id)
    try:
        await upsert_game(yaml.safe_load(document), player, dao, dcf)
    except ScenarioNotCorrect as e:
        await m.reply(f"Ошибка {e}\n попробуйте исправить файл")
        logger.error("game scenario from player %s has problems", player.id, exc_info=e)
        return
    await m.reply("Успешно сохранено")


async def get_manage(_: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MyGamesPanel.choose_game, mode=StartMode.RESET_STACK)


def setup(dp: Dispatcher):
    router.message.filter(
        GameStatusFilter(running=False),  # TODO can_be_author=True
    )

    router.message.register(cmd_save_game, ContentTypesFilter(content_types="document"))
    # TODO refactor it filters^ (state?)
    router.message.register(get_manage, Command(commands="my_games"))
    dp.include_router(router)
