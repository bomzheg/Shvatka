import typing
from io import BytesIO
from typing import BinaryIO

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models.dto.hints import (
    BaseHint,
    TextHint,
    GPSHint,
    ContactHint,
    PhotoHint,
    VenueHint,
    AudioHint,
    VideoHint,
    DocumentHint,
    AnimationHint,
    VoiceHint,
    VideoNoteHint,
    StickerHint,
)
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.tgbot.models.hint import (
    BaseHintLinkView,
    BaseHintContentView,
    TextHintView,
    GPSHintView,
    ContactHintView,
    PhotoLinkView,
    PhotoContentView,
    VenueHintView,
    AudioLinkView,
    AudioContentView,
    VideoLinkView,
    VideoContentView,
    DocumentLinkView,
    DocumentContentView,
    AnimationContentView,
    AnimationLinkView,
    VoiceLinkView,
    VoiceContentView,
    VideoNoteContentView,
    VideoNoteLinkView,
    StickerHintLinkView,
    StickerHintContentView,
)


class HintContentResolver:
    def __init__(self, dao: FileInfoDao, file_storage: FileStorage) -> None:
        self.dao = dao
        self.storage = file_storage

    async def resolve_link(self, hint_: BaseHint) -> BaseHintLinkView:
        match hint_:
            case TextHint(text=text):
                return TextHintView(
                    text=text,
                    link_preview=hint_.link_preview,
                )
            case GPSHint(latitude=latitude, longitude=longitude):
                return GPSHintView(
                    latitude=latitude,
                    longitude=longitude,
                )
            case VenueHint():
                hint_ = typing.cast(VenueHint, hint_)
                return VenueHintView(
                    latitude=hint_.latitude,
                    longitude=hint_.longitude,
                    title=hint_.title,
                    address=hint_.address,
                    foursquare_id=hint_.foursquare_id,
                    foursquare_type=hint_.foursquare_type,
                )
            case PhotoHint():
                hint_ = typing.cast(PhotoHint, hint_)
                return PhotoLinkView(
                    file_id=await self._resolve_file_id(hint_.file_guid),
                    show_caption_above_media=hint_.show_caption_above_media,
                    caption=hint_.caption,
                )
            case AudioHint():
                hint_ = typing.cast(AudioHint, hint_)
                return AudioLinkView(
                    file_id=await self._resolve_file_id(hint_.file_guid),
                    caption=hint_.caption,
                    thumb=await self._resolve_thumb_file_id(hint_.thumb_guid),
                )
            case VideoHint():
                hint_ = typing.cast(VideoHint, hint_)
                return VideoLinkView(
                    file_id=await self._resolve_file_id(hint_.file_guid),
                    caption=hint_.caption,
                    show_caption_above_media=hint_.show_caption_above_media,
                    thumb=await self._resolve_thumb_file_id(hint_.thumb_guid),
                )
            case DocumentHint():
                hint_ = typing.cast(DocumentHint, hint_)
                return DocumentLinkView(
                    file_id=await self._resolve_file_id(hint_.file_guid),
                    caption=hint_.caption,
                    thumb=await self._resolve_thumb_file_id(hint_.thumb_guid),
                )
            case AnimationHint():
                hint_ = typing.cast(AnimationHint, hint_)
                return AnimationLinkView(
                    file_id=await self._resolve_file_id(hint_.file_guid),
                    caption=hint_.caption,
                    show_caption_above_media=hint_.show_caption_above_media,
                    thumb=await self._resolve_thumb_file_id(hint_.thumb_guid),
                )
            case VoiceHint():
                hint_ = typing.cast(VoiceHint, hint_)
                return VoiceLinkView(
                    file_id=await self._resolve_file_id(hint_.file_guid),
                    caption=hint_.caption,
                )
            case VideoNoteHint(file_guid=guid):
                return VideoNoteLinkView(
                    file_id=await self._resolve_file_id(guid),
                )
            case ContactHint():
                hint_ = typing.cast(ContactHint, hint_)
                return ContactHintView(
                    phone_number=hint_.phone_number,
                    first_name=hint_.first_name,
                    last_name=hint_.last_name,
                    vcard=hint_.vcard,
                )
            case StickerHint(file_guid=guid):
                return StickerHintLinkView(
                    file_id=await self._resolve_file_id(guid),
                )
            case _:
                raise RuntimeError("unknown hint type")

    async def _resolve_file_id(self, guid: str) -> str:
        tg_link = (await self.dao.get_by_guid(guid)).tg_link
        return tg_link.file_id

    async def _resolve_thumb_file_id(self, guid: str | None) -> str | None:
        if guid is None:
            return None
        return await self._resolve_file_id(guid)

    async def resolve_content(self, hint_: BaseHint) -> BaseHintContentView:
        match hint_:
            case TextHint(text=text):
                return TextHintView(
                    text=text,
                    link_preview=hint_.link_preview,
                )
            case GPSHint(latitude=latitude, longitude=longitude):
                return GPSHintView(
                    latitude=latitude,
                    longitude=longitude,
                )
            case VenueHint():
                hint_ = typing.cast(VenueHint, hint_)
                return VenueHintView(
                    latitude=hint_.latitude,
                    longitude=hint_.longitude,
                    title=hint_.title,
                    address=hint_.address,
                    foursquare_id=hint_.foursquare_id,
                    foursquare_type=hint_.foursquare_type,
                )
            case PhotoHint():
                hint_ = typing.cast(PhotoHint, hint_)
                return PhotoContentView(
                    content=await self._resolve_bytes(hint_.file_guid),
                    show_caption_above_media=hint_.show_caption_above_media,
                    caption=hint_.caption,
                )
            case AudioHint():
                hint_ = typing.cast(AudioHint, hint_)
                return AudioContentView(
                    content=await self._resolve_bytes(hint_.file_guid),
                    caption=hint_.caption,
                )
            case VideoHint():
                hint_ = typing.cast(VideoHint, hint_)
                return VideoContentView(
                    content=await self._resolve_bytes(hint_.file_guid),
                    show_caption_above_media=hint_.show_caption_above_media,
                    caption=hint_.caption,
                )
            case DocumentHint():
                hint_ = typing.cast(DocumentHint, hint_)
                return DocumentContentView(
                    content=await self._resolve_bytes(hint_.file_guid),
                    caption=hint_.caption,
                    thumb=await self._resolve_thumb_bytes(hint_.thumb_guid),
                )
            case AnimationHint():
                hint_ = typing.cast(AnimationHint, hint_)
                return AnimationContentView(
                    content=await self._resolve_bytes(hint_.file_guid),
                    caption=hint_.caption,
                    show_caption_above_media=hint_.show_caption_above_media,
                    thumb=await self._resolve_thumb_bytes(hint_.thumb_guid),
                )
            case VoiceHint():
                hint_ = typing.cast(VoiceHint, hint_)
                return VoiceContentView(
                    content=await self._resolve_bytes(hint_.file_guid),
                    caption=hint_.caption,
                )
            case VideoNoteHint(file_guid=guid):
                return VideoNoteContentView(
                    content=await self._resolve_bytes(guid),
                )
            case ContactHint():
                hint_ = typing.cast(ContactHint, hint_)
                return ContactHintView(
                    phone_number=hint_.phone_number,
                    first_name=hint_.first_name,
                    last_name=hint_.last_name,
                    vcard=hint_.vcard,
                )
            case StickerHint(file_guid=guid):
                return StickerHintContentView(
                    content=await self._resolve_bytes(guid),
                )
            case _:
                raise RuntimeError("unknown hint type")

    async def _resolve_bytes(self, guid: str) -> BinaryIO:
        file_info = await self.dao.get_by_guid(guid)
        content = await self.storage.get(file_info.file_content_link)
        content = BytesWithName(content.read(), original_filename=file_info.public_filename)
        return content

    async def _resolve_thumb_bytes(self, guid: str | None) -> BinaryIO | None:
        if guid is None:
            return None
        return await self._resolve_bytes(guid)


class BytesWithName(BytesIO):
    def __init__(self, *args, **kwargs) -> None:
        self._name = kwargs.pop("original_filename", "")
        super().__init__(*args, **kwargs)

    @property
    def name(self) -> str:
        return self._name
