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
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda _, __: ScheduledContextHolder.dishka,
        is_async=True,
    )
