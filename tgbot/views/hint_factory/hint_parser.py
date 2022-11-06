from io import BytesIO
from uuid import uuid4

from aiogram import Bot
from aiogram.types import Message, ContentType

from db.dao import FileInfoDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.models.dto.scn import BaseHint, TextHint, GPSHint, FileContent, TgLink, FileContentLink, PhotoHint
from shvatka.models.dto.scn.hint_part import VenueHint, AudioHint
from shvatka.models.enums.hint_type import HintType


class HintParser:
    def __init__(self, dao: FileInfoDao, file_storage: FileStorage, bot: Bot):
        self.bot = bot
        self.dao = dao
        self.storage = file_storage

    def parse(self, message: Message, author: dto.Player) -> BaseHint:
        match message.content_type:
            case ContentType.TEXT:
                return TextHint(text=message.html_text)
            case ContentType.LOCATION:
                return GPSHint(longitude=message.location.longitude, latitude=message.location.latitude)
            case ContentType.VENUE:
                return VenueHint(
                    latitude=message.venue.location.latitude,
                    longitude=message.venue.location.longitude,
                    title=message.venue.title,
                    address=message.venue.address,
                    foursquare_id=message.venue.foursquare_id,
                    foursquare_type=message.venue.foursquare_type,
                )
            case ContentType.PHOTO:
                file_meta = await self.save_content(
                    file_id=message.photo[-1].file_id,
                    content_type=HintType.photo,
                    author=author,
                )
                return PhotoHint(caption=message.caption, file_guid=file_meta.guid)
            case ContentType.AUDIO:
                file_meta = await self.save_content(
                    file_id=message.audio.file_id,
                    content_type=HintType.audio,
                    author=author,
                )
                thumb = await self.save_content(
                    file_id=message.audio.thumb.file_id,
                    content_type=HintType.photo,
                    author=author,
                )
                return AudioHint(caption=message.caption, file_guid=file_meta.guid, thumb_guid=thumb.guid)
            case ContentType.VIDEO:
                pass
            case ContentType.DOCUMENT:
                pass
            case ContentType.ANIMATION:
                pass
            case ContentType.VOICE:
                pass
            case ContentType.VIDEO_NOTE:
                pass
            case ContentType.CONTACT:
                pass
            case ContentType.STICKER:
                pass
            case _:
                raise ValueError()

    async def save_content(self, file_id: str, content_type: HintType, author: dto.Player) -> FileContent:
        content = await self.bot.download(file_id, BytesIO())
        file_meta = FileContent(
            guid=str(uuid4()),
            original_filename="unknown",
            extension="",
            tg_link=TgLink(file_id=file_id, content_type=content_type),
            file_content_link=FileContentLink(file_path=""),
        )
        file_link = await self.storage.put(file_meta.local_file_name, content)
        file_meta.file_content_link = file_link
        await self.dao.upsert(file_meta, author)
        return file_meta
