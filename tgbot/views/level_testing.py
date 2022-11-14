from dataclasses import dataclass

from aiogram import Bot

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.views.level import LevelView
from tgbot.views.hint_sender import HintSender, create_hint_sender


@dataclass
class LevelBotView(LevelView):
    bot: Bot
    hint_sender: HintSender

    async def send_puzzle(self, suite: dto.LevelTestSuite) -> None:
        pass

    async def send_hint(self, suite: dto.LevelTestSuite, hint_number: int) -> None:
        pass

    async def correct_key(self, suite: dto.LevelTestSuite, key: str) -> None:
        pass

    async def wrong_key(self, suite: dto.LevelTestSuite, key: str) -> None:
        pass

    async def level_finished(self, suite: dto.LevelTestSuite) -> None:
        pass


def create_level_test_view(bot: Bot, dao: HolderDao, storage: FileStorage) -> LevelView:
    return LevelBotView(
        bot=bot,
        hint_sender=create_hint_sender(bot=bot, dao=dao, storage=storage),
    )
