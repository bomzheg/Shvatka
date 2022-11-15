from dataclasses import dataclass

from aiogram import Bot
from aiogram.utils.markdown import html_decoration as hd

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
        await self.hint_sender.send_hints(
            chat_id=suite.tester.player.user.tg_id,
            hint_containers=suite.level.get_hint(0).hint,
            caption=hd.bold(f"Тестирование уровня {suite.level.name_id}")
        )

    async def send_hint(self, suite: dto.LevelTestSuite, hint_number: int) -> None:
        hint = suite.level.get_hint(hint_number)
        if suite.level.is_last_hint(hint_number):
            hint_caption = f"Последняя подсказка уровня {suite.level.name_id} ({hint.time} мин.):\n"
        else:
            hint_caption = f"Уровень {suite.level.name_id}. Подсказка ({hint.time} мин.):\n"
        await self.hint_sender.send_hints(
            chat_id=suite.tester.player.user.tg_id,
            hint_containers=hint.hint,
            caption=hint_caption
        )

    async def correct_key(self, suite: dto.LevelTestSuite, key: str) -> None:
        await self.bot.send_message(
            chat_id=suite.tester.player.user.tg_id,
            text=f"Ключ {hd.pre(key)} верный! Поздравляю!",
        )

    async def wrong_key(self, suite: dto.LevelTestSuite, key: str) -> None:
        await self.bot.send_message(
            chat_id=suite.tester.player.user.tg_id,
            text=f"Ключ {hd.pre(key)} неверный.",
        )

    async def level_finished(self, suite: dto.LevelTestSuite) -> None:
        await self.bot.send_message(
            chat_id=suite.tester.player.user.tg_id,
            text=f"Тестирование уровня завершено, поздравляю!",
        )


def create_level_test_view(bot: Bot, dao: HolderDao, storage: FileStorage) -> LevelView:
    return LevelBotView(
        bot=bot,
        hint_sender=create_hint_sender(bot=bot, dao=dao, storage=storage),
    )
