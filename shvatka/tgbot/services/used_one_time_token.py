from dataclasses import dataclass

from aiogram import Bot
from aiogram_dialog import BgManagerFactory

from shvatka.infrastructure.bus.in_memory import UsedOneTimeTokenInteractor
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states


@dataclass
class UsedOneTimeTokenInteractorImpl(UsedOneTimeTokenInteractor):
    bg_manager_factory: BgManagerFactory
    bot: Bot
    dao: HolderDao

    async def __call__(self, player_id: int) -> None:
        player = await self.dao.player.get_by_id(player_id)
        user_id = player.get_chat_id()
        if user_id is None:
            return
        bg = self.bg_manager_factory.bg(bot=self.bot, user_id=user_id, chat_id=user_id)
        async with bg.fg() as fg:
            if fg.current_context().state == states.ProfileSG.one_time_login:
                await fg.done()
