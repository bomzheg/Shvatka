import logging
import typing
from typing import BinaryIO

from aiogram import Bot
from aiogram.types import BufferedInputFile

from shvatka.core.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.tgbot.views import hint_sender
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser

logger = logging.getLogger(__name__)


class BotFileGateway(FileGateway):
    def __init__(
        self, file_storage: FileStorage, bot: Bot, hint_parser: HintParser, tech_chat_id: int
    ):
        self.storage = file_storage
        self.bot = bot
        self.hint_parser = hint_parser
        self.tech_chat_id = tech_chat_id

    async def put(
        self, file_meta: scn.UploadedFileMeta, content: BinaryIO, author: dto.Player
    ) -> scn.FileMeta:
        if not file_meta.tg_link:
            return await self.renew_file_id(author, content, file_meta)
        return await self.storage.put(file_meta, content)

    async def get(self, file: scn.FileMeta) -> BinaryIO:
        try:
            return await self.storage.get(file.file_content_link)
        except (IOError, OSError):
            content = await self.bot.download(file=file.tg_link.file_id)
            return content

    async def renew_file_id(
        self, author: dto.Player, content: BinaryIO, file_meta: scn.UploadedFileMeta
    ) -> scn.FileMeta:
        assert file_meta.content_type is not None
        msg = await hint_sender.METHODS[file_meta.content_type](  # type: ignore[operator]
            self.bot,
            author.get_tech_chat_id(reserve_chat_id=self.tech_chat_id),
            BufferedInputFile(file=content.read(), filename=file_meta.public_filename),
        )
        await msg.delete()
        # TODO parser must only parse!
        saved_file = await self.hint_parser.save_file(msg, author, file_meta.guid)
        return typing.cast(scn.FileMeta, saved_file)
