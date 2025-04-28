from typing import Any

from adaptix import Retort
from dataclass_factory import Factory
from dishka import AsyncContainer
from telegraph.aio import Telegraph

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture import ResultsPainter
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.hint_sender import HintSender


async def warm_up(dishka: AsyncContainer) -> None:
    async with dishka() as request_dishka:
        deps: list[Any] = [
            HolderDao,
            Scheduler,
            FileStorage,
            UserGetter,
            Retort,
            Factory,
            Telegraph,
            HintParser,
            HintSender,
            ResultsPainter,
        ]
        for dep in deps:
            await request_dishka.get(dep)
