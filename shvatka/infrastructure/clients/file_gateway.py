import logging
from io import BytesIO
from typing import BinaryIO

from aiogram import Bot
from aiogram.types import BufferedInputFile

from shvatka.core.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
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
    ):
        self.storage = file_storage
        self.dao = dao
        self.bot = bot
        self.tech_chat_id = tech_chat_id

    async def put(self, file_meta: scn.UploadedFileMeta, content: BinaryIO, author: dto.Player):
        if not file_meta.tg_link:
            await self.upload_to_tg(author, content, file_meta)
        saved_file = await self.storage.put(file_meta, content)
        await self.dao.upsert(saved_file, author)

    async def get(self, file: scn.FileMeta) -> BinaryIO:
        try:
            return await self.storage.get(file.file_content_link)
        except (IOError, OSError):
            return await self.download_from_tg(tg_link=file.tg_link)

    async def renew_file_id(self, author: dto.Player, file_meta: scn.SavedFileMeta):
        return await self.upload_to_tg(
            author=author,
            content=await self.storage.get(file_meta.file_content_link),
            file_meta=file_meta,
        )

    async def upload_to_tg(
        self, author: dto.Player, content: BinaryIO, file_meta: scn.FileMetaLightweight
    ):
        assert file_meta.content_type is not None
        msg = await hint_sender.METHODS[file_meta.content_type](
            self.bot,
            author.get_tech_chat_id(reserve_chat_id=self.tech_chat_id),
            BufferedInputFile(file=content.read(), filename=file_meta.public_filename),
        )
        await msg.delete()
        tg_link = parse_message(msg)
        assert tg_link
        await self.dao.update_file_id(file_meta.guid, tg_link.file_id)

    async def download_from_tg(self, tg_link: scn.TgLink) -> BinaryIO:
        result = await self.bot.download(tg_link.file_id, BytesIO())
        if not result:
            raise IOError
        return result
