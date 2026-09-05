import asyncio

from aiogram import Bot
from aiogram.types import BufferedInputFile

from shvatka.core.interfaces.dal.complex import GameStatDao
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services.game import get_full_game
from shvatka.core.services.game_stat import get_game_stat
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture import paint_it
from shvatka.tgbot.config.models.bot import BotConfig


class ResultsPainter:
    def __init__(
        self, bot: Bot, dao: HolderDao, game_stat: GameStatDao, config: BotConfig
    ) -> None:
        self.bot = bot
        self.dao = dao
        self.game_stat = game_stat
        self.chat_id = config.log_chat

    async def get_game_results(self, game: dto.Game, identity: IdentityProvider) -> str:
        if game.results.results_picture_file_id:
            return game.results.results_picture_file_id
        current_game = await get_full_game(
            id_=game.id,
            identity=identity,
            dao=self.dao.game,
        )
        game_stat = await get_game_stat(current_game, identity, self.game_stat)
        return await self.paint_game_results(current_game, game_stat)

    async def paint_game_results(self, game: dto.FullGame, game_stat: dto.GameStat) -> str:
        if game.results.results_picture_file_id:
            return game.results.results_picture_file_id
        # matplotlib is seconds of drawing; on the loop it is seconds in
        # which nothing else in the process is served
        picture = await asyncio.to_thread(paint_it, game_stat, game)
        msg = await self.bot.send_photo(
            self.chat_id, BufferedInputFile(picture.read(), "results.png")
        )
        await msg.delete()
        assert msg.photo
        photo_file_id = msg.photo[-1].file_id
        await self.dao.game.set_results_photo(game, photo_file_id)
        await self.dao.commit()
        return photo_file_id
