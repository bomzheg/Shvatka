import typing
from dataclasses import dataclass, field

from aiogram import Bot
from dishka import Provider, Scope, provide

from shvatka.core.interfaces.clients.file_storage import FileGateway, FileStorage
from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.utils.exceptions import FileRejectedByTelegram
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao

SENT_FILE_ID = "sent-to-telegram"


@dataclass
class FakeTelegram:
    refuse: bool = False
    """refuse every file, the way telegram refuses one too large to send"""
    refused_guids: set[str] = field(default_factory=set)
    """refuse only these, when a test knows the guid up front"""
    reason: str = "Request Entity Too Large"
    sent: list[str] = field(default_factory=list)
    """guids of the files telegram was asked to take, refused ones included"""

    def refuses(self, guid: str) -> bool:
        return self.refuse or guid in self.refused_guids

    def clear(self) -> None:
        self.refuse = False
        self.refused_guids.clear()
        self.sent.clear()


class FileGatewayMock(BotFileGateway):
    def __init__(
        self, file_storage: FileStorage, dao: FileInfoDao, telegram: FakeTelegram
    ) -> None:
        super().__init__(
            file_storage=file_storage,
            dao=dao,
            bot=typing.cast(Bot, None),
            tech_chat_id=0,
        )
        self.telegram = telegram

    async def upload_to_tg(
        self, author: dto.Player, content: typing.BinaryIO, file_meta: hints.FileMetaLightweight
    ) -> None:
        # the real one reads the whole stream to send it; callers rely on that
        content.read()
        self.telegram.sent.append(file_meta.guid)
        if self.telegram.refuses(file_meta.guid):
            raise FileRejectedByTelegram(
                text=f"telegram rejected file {file_meta.guid}",
                guid=file_meta.guid,
                filename=file_meta.public_filename,
                reason=self.telegram.reason,
            )
        await self.dao.update_file_id(file_meta.guid, SENT_FILE_ID)

    async def download_from_tg(self, tg_link: hints.TgLink) -> typing.BinaryIO:
        raise NotImplementedError("nothing is downloaded from the fake telegram")


class FileGatewayMockProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def telegram(self) -> FakeTelegram:
        return FakeTelegram()

    @provide(override=True)
    def file_gateway(
        self, storage: FileStorage, dao: HolderDao, telegram: FakeTelegram
    ) -> FileGateway:
        return FileGatewayMock(file_storage=storage, dao=dao.file_info, telegram=telegram)
