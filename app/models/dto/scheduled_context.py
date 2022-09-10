from dataclasses import dataclass

from aiogram import Bot

from app.dao.holder import HolderDao


@dataclass
class ScheduledContext:
    dao: HolderDao
    bot: Bot
