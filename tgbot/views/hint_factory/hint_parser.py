from io import BytesIO
from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from aiogram.types import Message, ContentType, PhotoSize

from infrastructure.db.dao import FileInfoDao
from shvatka.interfaces.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.models.dto import scn
from shvatka.models.dto.scn import (
    BaseHint,
    TextHint,
    GPSHint,
    FileMeta,
    TgLink,
    PhotoHint,
    UploadedFileMeta,
)
from shvatka.models.dto.scn.hint_part import (
    VenueHint,
    AudioHint,
    VideoHint,
    DocumentHint,
    AnimationHint,
    VoiceHint,
    VideoNoteHint,
    ContactHint,
    StickerHint,
)
from shvatka.models.enums.hint_type import HintType


class HintParser:
    def __init__(self, dao: FileInfoDao, file_storage: FileStorage, bot: Bot):
        self.bot = bot
        self.dao = dao
        self.storage = file_storage

    async def parse(self, message: Message, author: dto.Player) -> BaseHint:
        file_meta = await self.save_file(
            message=message,
            author=author,
            guid=(str(uuid4())),
        )
        match message.content_type:
            case ContentType.TEXT:
                return TextHint(text=message.html_text)
            case ContentType.LOCATION:
                return GPSHint(
                    longitude=message.location.longitude, latitude=message.location.latitude
                )
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
                return PhotoHint(caption=message.html_text, file_guid=file_meta.guid)
            case ContentType.AUDIO:
                thumb = await self.save_thumb(author, message.audio.thumb)
                return AudioHint(
                    caption=message.html_text,
                    file_guid=file_meta.guid,
                    thumb_guid=thumb.guid if thumb else None,
                )
            case ContentType.VIDEO:
                thumb = await self.save_thumb(author, message.video.thumb)
                return VideoHint(
                    caption=message.html_text,
                    file_guid=file_meta.guid,
                    thumb_guid=thumb.guid if thumb else None,
                )
            case ContentType.DOCUMENT:
                thumb = await self.save_thumb(author, message.document.thumb)
                return DocumentHint(
                    caption=message.html_text,
                    file_guid=file_meta.guid,
                    thumb_guid=thumb.guid if thumb else None,
                )
            case ContentType.ANIMATION:
                thumb = await self.save_thumb(author, message.animation.thumb)
                return AnimationHint(
                    caption=message.html_text,
                    file_guid=file_meta.guid,
                    thumb_guid=thumb.guid if thumb else None,
                )
            case ContentType.VOICE:
                return VoiceHint(caption=message.html_text, file_guid=file_meta.guid)
            case ContentType.VIDEO_NOTE:
                return VideoNoteHint(file_guid=file_meta.guid)
            case ContentType.CONTACT:
                return ContactHint(
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name,
                    vcard=message.contact.vcard,
                )
            case ContentType.STICKER:
                return StickerHint(file_guid=file_meta.guid)
            case _:
                raise ValueError()

    async def save_file(self, message: Message, author: dto.Player, guid: str) -> scn.FileMeta | None:
        match message.content_type:
            case ContentType.PHOTO:
                return await self.save_content(
                    file_id=message.photo[-1].file_id,
                    content_type=HintType.photo,
                    author=author,
                    guid=guid,
                )
            case ContentType.AUDIO:
                return await self.save_content(
                    file_id=message.audio.file_id,
                    content_type=HintType.audio,
                    author=author,
                    filename=message.audio.file_name,
                    guid=guid,
                )
            case ContentType.VIDEO:
                return await self.save_content(
                    file_id=message.video.file_id,
                    content_type=HintType.video,
                    author=author,
                    filename=message.video.file_name,
                    guid=guid,
                )
            case ContentType.DOCUMENT:
                return await self.save_content(
                    file_id=message.document.file_id,
                    content_type=HintType.document,
                    author=author,
                    filename=message.document.file_name,
                    guid=guid,
                )
            case ContentType.ANIMATION:
                return await self.save_content(
                    file_id=message.animation.file_id,
                    content_type=HintType.animation,
                    author=author,
                    filename=message.animation.file_name,
                    guid=guid,
                )
            case ContentType.VOICE:
                return await self.save_content(
                    file_id=message.voice.file_id,
                    content_type=HintType.voice,
                    author=author,
                    guid=guid,
                )
            case ContentType.VIDEO_NOTE:
                return await self.save_content(
                    file_id=message.video_note.file_id,
                    content_type=HintType.video_note,
                    author=author,
                    guid=guid,
                )
            case ContentType.STICKER:
                return await self.save_content(
                    file_id=message.sticker.file_id,
                    content_type=HintType.sticker,
                    author=author,
                    guid=guid,
                )
            case _:
                return None

    async def save_thumb(self, author: dto.Player, thumb: PhotoSize | None):
        if thumb:
            return await self.save_content(
                file_id=thumb.file_id,
                content_type=HintType.photo,
                author=author,
                guid=str(uuid4()),
            )
        return None

    async def save_content(
        self,
        file_id: str,
        content_type: HintType,
        author: dto.Player,
        guid: str,
        filename: str = "unknown",
    ) -> FileMeta:
        content = await self.bot.download(file_id, BytesIO())
        extension = "".join(Path(filename).suffixes)
        file_meta = UploadedFileMeta(
            guid=guid,
            original_filename=get_name_without_extension(filename, extension),
            extension=extension,
            tg_link=TgLink(file_id=file_id, content_type=content_type),
        )
        stored_file = await self.storage.put(file_meta, content)
        await self.dao.upsert(stored_file, author)
        await self.dao.commit()
        return stored_file


def get_name_without_extension(name: str, extension: str) -> str:
    if not extension:
        return name
    return name[: -len(extension)]
