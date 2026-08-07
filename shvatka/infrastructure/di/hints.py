"""Sending hints to telegram — shared by the bot and the api.

Both edges announce game releases (the api when the author starts collecting
waivers from the site, the bot when they do it from the chat), and announcing
means sending hints, so these live here rather than in the bot-only providers.
"""

from typing import AsyncIterable

from aiogram import Bot
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.views.game import GameReleasePublisher
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.game_release import GameBotReleasePublisher
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_sender import HintSender


class HintSenderProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_hint_content_resolver(
        self, dao: HolderDao, file_storage: FileStorage
    ) -> HintContentResolver:
        return HintContentResolver(dao=dao.file_info, file_storage=file_storage)

    @provide
    async def get_hint_sender(
        self,
        bot: Bot,
        resolver: HintContentResolver,
        pool: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[HintSender]:
        # dedicated session so renewed file_ids are committed in their own
        # transaction, independently of the request-scoped HolderDao session
        async with pool() as session:
            yield HintSender(
                bot=bot,
                resolver=resolver,
                file_info_dao=FileInfoDao(session),
            )


class GameReleasePublisherProvider(Provider):
    """Kept apart from the sender so tests can announce into a mock."""

    scope = Scope.REQUEST

    @provide
    def get_release_publisher(
        self,
        bot: Bot,
        hint_sender: HintSender,
        resolver: HintContentResolver,
        config: BotConfig,
    ) -> GameReleasePublisher:
        return GameBotReleasePublisher(
            bot=bot,
            hint_sender=hint_sender,
            resolver=resolver,
            log_chat_id=config.game_log_chat,
        )
