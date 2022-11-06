from io import BytesIO
from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from aiogram.types import Message, ContentType

from db.dao import FileInfoDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.models.dto.scn import BaseHint, TextHint, GPSHint, FileMeta, TgLink, FileContentLink, PhotoHint
from shvatka.models.dto.scn.hint_part import VenueHint, AudioHint, VideoHint, DocumentHint, AnimationHint, VoiceHint, \
    VideoNoteHint, ContactHint, StickerHint
from shvatka.models.enums.hint_type import HintType


class HintParser:
    def __init__(self, dao: FileInfoDao, file_storage: FileStorage, bot: Bot):
        self.bot = bot
        self.dao = dao
        self.storage = file_storage

    async def parse(self, message: Message, author: dto.Player) -> BaseHint:
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
                return PhotoHint(caption=message.html_text, file_guid=file_meta.guid)
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
                return AudioHint(caption=message.html_text, file_guid=file_meta.guid, thumb_guid=thumb.guid)
            case ContentType.VIDEO:
                file_meta = await self.save_content(
                    file_id=message.video.file_id,
                    content_type=HintType.video,
                    author=author,
                )
                thumb = await self.save_content(
                    file_id=message.video.thumb.file_id,
                    content_type=HintType.video,
                    author=author,
                )
                return VideoHint(caption=message.html_text, file_guid=file_meta.guid, thumb_guid=thumb.guid)
            case ContentType.DOCUMENT:
                file_meta = await self.save_content(
                    file_id=message.document.file_id,
                    content_type=HintType.document,
                    author=author,
                )
                thumb = await self.save_content(
                    file_id=message.document.thumb.file_id,
                    content_type=HintType.document,
                    author=author,
                )
                return DocumentHint(caption=message.html_text, file_guid=file_meta.guid, thumb_guid=thumb.guid)
            case ContentType.ANIMATION:
                file_meta = await self.save_content(
                    file_id=message.animation.file_id,
                    content_type=HintType.animation,
                    author=author,
                )
                thumb = await self.save_content(
                    file_id=message.animation.thumb.file_id,
                    content_type=HintType.animation,
                    author=author,
                )
                return AnimationHint(caption=message.html_text, file_guid=file_meta.guid, thumb_guid=thumb.guid)
            case ContentType.VOICE:
                file_meta = await self.save_content(
                    file_id=message.voice.file_id,
                    content_type=HintType.voice,
                    author=author,
                )
                return VoiceHint(caption=message.html_text, file_guid=file_meta.guid)
            case ContentType.VIDEO_NOTE:
                file_meta = await self.save_content(
                    file_id=message.video_note.file_id,
                    content_type=HintType.video_note,
                    author=author,
                )
                return VideoNoteHint(file_guid=file_meta.guid)
            case ContentType.CONTACT:
                return ContactHint(
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name,
                    vcard=message.contact.vcard,
                )
            case ContentType.STICKER:
                file_meta = await self.save_content(
                    file_id=message.sticker.file_id,
                    content_type=HintType.sticker,
                    author=author,
                )
                return StickerHint(file_guid=file_meta.guid)
            case _:
                raise ValueError()

    async def save_content(
        self,
        file_id: str,
        content_type: HintType,
        author: dto.Player,
        filename: str = "unknown",
    ) -> FileMeta:
        content = await self.bot.download(file_id, BytesIO())
        extension = "".join(Path(filename).suffixes)
        file_meta = FileMeta(
            guid=str(uuid4()),
            original_filename=get_name_without_extension(filename, extension),
            extension=extension,
            tg_link=TgLink(file_id=file_id, content_type=content_type),
            file_content_link=FileContentLink(file_path=""),
        )
        file_link = await self.storage.put(file_meta.local_file_name, content)
        file_meta.file_content_link = file_link
        await self.dao.upsert(file_meta, author)
        await self.dao.commit()
        return file_meta


def get_name_without_extension(name: str, extension: str) -> str:
    if not extension:
        return name
    return name[:-len(extension)]
