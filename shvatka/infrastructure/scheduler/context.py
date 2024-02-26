from dataclasses import dataclass

from aiogram import Bot
from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.infrastructure.db.dao.holder import HolderDao


class ScheduledContextHolder:
    """
    ATTENTION!
    GLOBAL VARIABLE!
    """

    dishka: AsyncContainer


@dataclass
class ScheduledContext:
    dao: HolderDao  # need wrappers or protocols
    bot: Bot  # need wrappers or protocols
    file_storage: FileStorage
    scheduler: Scheduler
    game_log_chat: int


def inject(func):
    async def wrapper(*args, **kwargs):
        async with ScheduledContextHolder.dishka() as request_dishka:
            wrapped = wrap_injection(
                func=func,
                remove_depends=True,
                container_getter=lambda _, __: request_dishka,
                is_async=True,
            )
            return await wrapped(*args, **kwargs)

    return wrapper
