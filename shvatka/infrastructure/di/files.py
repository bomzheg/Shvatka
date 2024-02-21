from aiogram import Bot
from dishka import Provider, provide, Scope

from shvatka.common import FileStorageConfig
from shvatka.core.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.infrastructure.clients.factory import create_file_storage
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig


class FileClientProvider(Provider):
    scope = Scope.APP

    @provide
    def get_file_client(self, config: FileStorageConfig) -> FileStorage:
        return create_file_storage(config)

    @provide
    def get_file_gateway(
        self, storage: FileStorage, bot: Bot, dao: HolderDao, bot_config: BotConfig
    ) -> FileGateway:
        return BotFileGateway(
            file_storage=storage,
            bot=bot,
            dao=dao.file_info,
            tech_chat_id=bot_config.log_chat,
        )
