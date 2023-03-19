from aiogram import Bot
from aiogram.types import BufferedInputFile

from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture import paint_it


class ResultsPainter:
    def __init__(self, bot: Bot, dao: HolderDao, chat_id: int):
        self.bot = bot
        self.dao = dao
        self.chat_id = chat_id

    async def get_game_results(self, stats: dto.GameStat, game: dto.FullGame) -> str:
        # TODO check it already uploaded
        picture = paint_it(stats, game)
        msg = await self.bot.send_photo(
            self.chat_id, BufferedInputFile(picture.read(), "results.png")
        )
        # TODO save file_id
        await msg.delete()
        assert msg.photo
        return msg.photo[-1].file_id
