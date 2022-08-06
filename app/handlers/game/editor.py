import logging

import yaml
from aiogram import Router, Dispatcher, Bot
from aiogram.dispatcher.filters import ContentTypesFilter
from aiogram.types import Message
from dataclass_factory import Factory

from app.dao.holder import HolderDao
from app.filters.game_status import GameStatusFilter
from app.models import dto
from app.services.game import upsert_game
from app.utils.exceptions import ScenarioNotCorrect

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


def setup(dp: Dispatcher):
    router.message.filter(
        GameStatusFilter(active=False),  # TODO can_be_author=True
    )

    router.message.register(cmd_save_game, ContentTypesFilter(content_types="document"))
    # TODO refactor it filters^ (state?)
    dp.include_router(router)
