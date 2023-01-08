import logging
from typing import BinaryIO

from aiogram import Bot
from aiogram.types import BufferedInputFile

from shvatka.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.models import dto
from shvatka.models.dto import scn
from tgbot.views import hint_sender
from tgbot.views.hint_factory.hint_parser import HintParser

logger = logging.getLogger(__name__)


class BotFileGateway(FileGateway):
    def __init__(self, file_storage: FileStorage, bot: Bot, hint_parser: HintParser):
        self.storage = file_storage
        self.bot = bot
        self.hint_parser = hint_parser

    async def put(
        self, file_meta: scn.UploadedFileMeta, content: BinaryIO, author: dto.Player
    ) -> scn.FileMeta:
        if not file_meta.tg_link:
            msg = await hint_sender.METHODS[file_meta.content_type](
                self.bot,
                author.user.tg_id,
                BufferedInputFile(file=content.read(), filename=file_meta.public_filename),
            )
            await msg.delete()
            saved_file = await self.hint_parser.save_file(msg, author, file_meta.guid)
            return saved_file  # TODO parser must only parse!
        return await self.storage.put(file_meta, content)
