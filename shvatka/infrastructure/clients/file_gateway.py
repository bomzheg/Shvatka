import logging
from io import BytesIO
from typing import BinaryIO

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile

from shvatka.core.interfaces.clients.file_storage import FileGateway, FileStorage
from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.utils.exceptions import FileRejectedByTelegram
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.tgbot.views import hint_sender
from shvatka.tgbot.views.hint_factory.hint_parser import parse_message

logger = logging.getLogger(__name__)


class BotFileGateway(FileGateway):
    def __init__(
        self,
        file_storage: FileStorage,
        dao: FileInfoDao,
        bot: Bot,
        tech_chat_id: int,
    ) -> None:
        self.storage = file_storage
        self.dao = dao
        self.bot = bot
        self.tech_chat_id = tech_chat_id

    async def put(self, file_meta: hints.UploadedFileMeta, content: BinaryIO, author: dto.Player):
        if file_meta.tg_link:
            saved_file = await self.storage.put(file_meta, content)
            await self.dao.upsert(saved_file, author)
            return
        # both the storage and telegram read the whole stream, so buffer it once
        data = content.read()
        saved_file = await self.storage.put(file_meta, BytesIO(data))
        await self.dao.upsert(saved_file, author)
        # sent after the row exists: the file_id telegram answers with is written
        # onto that row, and an update of a row that isn't there yet is lost.
        # A refusal raises with the row uncommitted, so nothing is kept either way.
        await self.upload_to_tg(author, BytesIO(data), file_meta)

    async def get(self, file: hints.FileMeta) -> BinaryIO:
        try:
            return await self.storage.get(file.file_content_link)
        except OSError:
            if file.tg_link is None:
                raise
            return await self.download_from_tg(tg_link=file.tg_link)

    async def renew_file_id(self, author: dto.Player, file_meta: hints.SavedFileMeta):
        return await self.upload_to_tg(
            author=author,
            content=await self.storage.get(file_meta.file_content_link),
            file_meta=file_meta,
        )

    async def upload_to_tg(
        self, author: dto.Player, content: BinaryIO, file_meta: hints.FileMetaLightweight
    ):
        assert file_meta.content_type is not None
        try:
            msg = await hint_sender.METHODS[file_meta.content_type](
                self.bot,
                author.get_tech_chat_id(reserve_chat_id=self.tech_chat_id),
                BufferedInputFile(file=content.read(), filename=file_meta.public_filename),
            )
        except TelegramAPIError as e:
            logger.warning("telegram rejected file %s", file_meta.guid, exc_info=e)
            raise FileRejectedByTelegram(
                text=f"telegram rejected file {file_meta.guid} "
                f"({file_meta.public_filename}): {e.message}",
                guid=file_meta.guid,
                filename=file_meta.public_filename,
                reason=e.message,
            ) from e
        await msg.delete()
        tg_link = parse_message(msg)
        assert tg_link
        await self.dao.update_file_id(file_meta.guid, tg_link.file_id)

    async def download_from_tg(self, tg_link: hints.TgLink) -> BinaryIO:
        result = await self.bot.download(tg_link.file_id, BytesIO())
        if not result:
            raise OSError
        return result
