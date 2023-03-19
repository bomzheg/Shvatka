from aiogram import Bot
from aiogram.types import BufferedInputFile

from shvatka.core.models import dto
from shvatka.core.services.game import get_full_game
from shvatka.core.services.game_stat import get_game_stat
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture import paint_it


class ResultsPainter:
    def __init__(self, bot: Bot, dao: HolderDao, chat_id: int):
        self.bot = bot
        self.dao = dao
        self.chat_id = chat_id

    async def get_game_results(self, game: dto.Game, player: dto.Player) -> str:
        # TODO check it already uploaded
        current_game = await get_full_game(
            id_=game.id,
            author=player,
            dao=self.dao.game,
        )
        game_stat = await get_game_stat(current_game, player, self.dao.game_stat)
        picture = paint_it(game_stat, current_game)
        msg = await self.bot.send_photo(
            self.chat_id, BufferedInputFile(picture.read(), "results.png")
        )
        # TODO save file_id
        await msg.delete()
        assert msg.photo
        return msg.photo[-1].file_id
