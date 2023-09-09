from io import BytesIO
from pathlib import Path
from uuid import uuid4

from aiogram import Bot
from aiogram.types import Message, ContentType, PhotoSize

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.models.dto.scn import (
    BaseHint,
    TextHint,
    GPSHint,
    FileMeta,
    TgLink,
    PhotoHint,
    UploadedFileMeta,
)
from shvatka.core.models.dto.scn.hint_part import (
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
from shvatka.core.models.enums.hint_type import HintType
from shvatka.infrastructure.db.dao import FileInfoDao


class HintParser:
    def __init__(self, dao: FileInfoDao, file_storage: FileStorage, bot: Bot) -> None:
        self.bot = bot
        self.dao = dao
        self.storage = file_storage

    async def parse(self, message: Message, author: dto.Player) -> BaseHint:
        guid = str(uuid4())
        await self.save_file(
            message=message,
            author=author,
            guid=guid,
        )
        match message.content_type:
            case ContentType.TEXT:
                return TextHint(text=message.html_text)
            case ContentType.LOCATION:
                assert message.location
                return GPSHint(
                    longitude=message.location.longitude, latitude=message.location.latitude
                )
            case ContentType.VENUE:
                assert message.venue
                return VenueHint(
                    latitude=message.venue.location.latitude,
                    longitude=message.venue.location.longitude,
                    title=message.venue.title,
                    address=message.venue.address,
                    foursquare_id=message.venue.foursquare_id,
                    foursquare_type=message.venue.foursquare_type,
                )
            case ContentType.PHOTO:
                return PhotoHint(caption=message.html_text, file_guid=guid)
            case ContentType.AUDIO:
                assert message.audio
                thumb = await self.save_thumb(author, message.audio.thumbnail)
                return AudioHint(
                    caption=message.html_text,
                    file_guid=guid,
                    thumb_guid=thumb.guid if thumb else None,
                )
            case ContentType.VIDEO:
                assert message.video
                thumb = await self.save_thumb(author, message.video.thumbnail)
                return VideoHint(
                    caption=message.html_text,
                    file_guid=guid,
                    thumb_guid=thumb.guid if thumb else None,
                )
            case ContentType.DOCUMENT:
                assert message.document
                thumb = await self.save_thumb(author, message.document.thumbnail)
                return DocumentHint(
                    caption=message.html_text,
                    file_guid=guid,
                    thumb_guid=thumb.guid if thumb else None,
                )
            case ContentType.ANIMATION:
                assert message.animation
                thumb = await self.save_thumb(author, message.animation.thumbnail)
                return AnimationHint(
                    caption=message.html_text,
                    file_guid=guid,
                    thumb_guid=thumb.guid if thumb else None,
                )
            case ContentType.VOICE:
                return VoiceHint(caption=message.html_text, file_guid=guid)
            case ContentType.VIDEO_NOTE:
                return VideoNoteHint(file_guid=guid)
            case ContentType.CONTACT:
                assert message.contact
                return ContactHint(
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name,
                    vcard=message.contact.vcard,
                )
            case ContentType.STICKER:
                return StickerHint(file_guid=guid)
            case _:
                raise ValueError

    async def save_file(
        self, message: Message, author: dto.Player, guid: str
    ) -> scn.FileMeta | None:
        tg_link = parse_message(message)
        if not tg_link:
            return None
        return await self.save_content(
            tg_link=tg_link,
            author=author,
            guid=guid,
        )

    async def save_thumb(self, author: dto.Player, thumb: PhotoSize | None):
        if thumb:
            return await self.save_content(
                tg_link=scn.ParsedTgLink(file_id=thumb.file_id, content_type=HintType.photo),
                author=author,
                guid=str(uuid4()),
            )
        return None

    async def save_content(
        self,
        tg_link: scn.ParsedTgLink,
        author: dto.Player,
        guid: str,
    ) -> FileMeta:
        filename = tg_link.filename or "unknown"
        content = await self.bot.download(tg_link.file_id, BytesIO())
        assert content is not None
        extension = "".join(Path(filename).suffixes)
        file_meta = UploadedFileMeta(
            guid=guid,
            original_filename=get_name_without_extension(filename, extension),
            extension=extension,
            tg_link=TgLink(file_id=tg_link.file_id, content_type=tg_link.content_type),
        )
        stored_file = await self.storage.put(file_meta, content)
        await self.dao.upsert(stored_file, author)
        await self.dao.commit()
        return stored_file


def parse_message(message: Message) -> scn.ParsedTgLink | None:
    match message.content_type:
        case ContentType.PHOTO:
            assert message.photo is not None
            return scn.ParsedTgLink(
                file_id=message.photo[-1].file_id,
                content_type=HintType.photo,
            )
        case ContentType.AUDIO:
            assert message.audio
            return scn.ParsedTgLink(
                file_id=message.audio.file_id,
                content_type=HintType.audio,
                filename=message.audio.file_name,
            )
        case ContentType.VIDEO:
            assert message.video
            return scn.ParsedTgLink(
                file_id=message.video.file_id,
                content_type=HintType.video,
                filename=message.video.file_name,
            )
        case ContentType.DOCUMENT:
            assert message.document
            return scn.ParsedTgLink(
                file_id=message.document.file_id,
                content_type=HintType.document,
                filename=message.document.file_name,
            )
        case ContentType.ANIMATION:
            assert message.animation
            return scn.ParsedTgLink(
                file_id=message.animation.file_id,
                content_type=HintType.animation,
                filename=message.animation.file_name,
            )
        case ContentType.VOICE:
            assert message.voice
            return scn.ParsedTgLink(
                file_id=message.voice.file_id,
                content_type=HintType.voice,
            )
        case ContentType.VIDEO_NOTE:
            assert message.video_note
            return scn.ParsedTgLink(
                file_id=message.video_note.file_id,
                content_type=HintType.video_note,
            )
        case ContentType.STICKER:
            assert message.sticker
            return scn.ParsedTgLink(
                file_id=message.sticker.file_id,
                content_type=HintType.sticker,
            )
        case _:
            return None


def get_name_without_extension(name: str, extension: str) -> str:
    if not extension:
        return name
    return name[: -len(extension)]
