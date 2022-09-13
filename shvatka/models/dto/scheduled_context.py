from dataclasses import dataclass

from aiogram import Bot

from shvatka.dao.holder import HolderDao


@dataclass
class ScheduledContext:
    dao: HolderDao
    bot: Bot
