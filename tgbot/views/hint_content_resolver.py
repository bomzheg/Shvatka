import typing
from io import BytesIO
from typing import BinaryIO

from db.dao import FileInfoDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models.dto.scn.hint_part import BaseHint, TextHint, GPSHint, ContactHint, PhotoHint, VenueHint, AudioHint, \
    VideoHint, DocumentHint, AnimationHint, VoiceHint, VideoNoteHint, StickerHint
from tgbot.models.hint import BaseHintLinkView, BaseHintContentView, TextHintView, GPSHintView, ContactHintView, \
    PhotoLinkView, PhotoContentView, VenueHintView, AudioLinkView, AudioContentView, VideoLinkView, VideoContentView, \
    DocumentLinkView, DocumentContentView, AnimationContentView, AnimationLinkView, VoiceLinkView, VoiceContentView, \
    VideoNoteContentView, VideoNoteLinkView, StickerHintView


class HintContentResolver:
    def __init__(self, dao: FileInfoDao, file_storage: FileStorage):
        self.dao = dao
        self.storage = file_storage

    async def resolve_link(self, hint: BaseHint) -> BaseHintLinkView:
        match hint:
            case TextHint(text=text):
                return TextHintView(text=text)
            case GPSHint(latitude=latitude, longitude=longitude):
                return GPSHintView(latitude=latitude, longitude=longitude)
            case VenueHint():
                hint = typing.cast(VenueHint, hint)
                return VenueHintView(
                    latitude=hint.latitude,
                    longitude=hint.longitude,
                    title=hint.title,
                    address=hint.address,
                    foursquare_id=hint.foursquare_id,
                    foursquare_type=hint.foursquare_type,
                )
            case PhotoHint():
                hint = typing.cast(PhotoHint, hint)
                return PhotoLinkView(file_id=await self._resolve_file_id(hint.file_guid), caption=hint.caption)
            case AudioHint(file_guid=guid, caption=caption, thumb_guid=thumb_guid):
                return AudioLinkView(
                    file_id=await self._resolve_file_id(guid),
                    caption=caption,
                    thumb=await self._resolve_file_id(thumb_guid),
                )
            case VideoHint(file_guid=guid, caption=caption, thumb_guid=thumb_guid):
                return VideoLinkView(
                    file_id=await self._resolve_file_id(guid),
                    caption=caption,
                    thumb=await self._resolve_file_id(thumb_guid),
                )
            case DocumentHint(file_guid=guid, caption=caption, thumb_guid=thumb_guid):
                return DocumentLinkView(
                    file_id=await self._resolve_file_id(guid),
                    caption=caption,
                    thumb=await self._resolve_file_id(thumb_guid),
                )
            case AnimationHint(file_guid=guid, caption=caption, thumb_guid=thumb_guid):
                return AnimationLinkView(
                    file_id=await self._resolve_file_id(guid),
                    caption=caption,
                    thumb=await self._resolve_file_id(thumb_guid),
                )
            case VoiceHint(file_guid=guid, caption=caption):
                return VoiceLinkView(file_id=await self._resolve_file_id(guid), caption=caption)
            case VideoNoteHint(file_guid=guid):
                return VideoNoteLinkView(file_id=await self._resolve_file_id(guid))
            case ContactHint(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                vcard=vcard,
            ):
                return ContactHintView(
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name,
                    vcard=vcard,
                )
            case StickerHint(file_guid=guid):
                return StickerHintView(file_id=await self._resolve_file_id(guid))

    async def _resolve_file_id(self, guid: str | None) -> str | None:
        if guid is None:
            return None
        tg_link = (await self.dao.get_by_guid(guid)).tg_link
        return tg_link.file_id

    async def resolve_content(self, hint: BaseHint) -> BaseHintContentView:
        match hint:
            case TextHint(text=text):
                return TextHintView(text=text)
            case GPSHint(latitude=latitude, longitude=longitude):
                return GPSHintView(latitude=latitude, longitude=longitude)
            case VenueHint(
                latitude=latitude,
                longitude=longitude,
                title=title,
                address=address,
                foursquare_id=foursquare_id,
                foursquare_type=foursquare_type,
            ):
                return VenueHintView(
                    latitude=latitude,
                    longitude=longitude,
                    title=title,
                    address=address,
                    foursquare_id=foursquare_id,
                    foursquare_type=foursquare_type,
                )
            case PhotoHint(file_guid=guid, caption=caption):
                return PhotoContentView(content=await self._resolve_bytes(guid), caption=caption)
            case AudioHint(file_guid=guid, caption=caption, thumb_guid=thumb_guid):
                return AudioContentView(
                    content=await self._resolve_bytes(guid),
                    caption=caption,
                    thumb=await self._resolve_bytes(thumb_guid),
                )
            case VideoHint(file_guid=guid, caption=caption, thumb_guid=thumb_guid):
                return VideoContentView(
                    content=await self._resolve_bytes(guid),
                    caption=caption,
                    thumb=await self._resolve_bytes(thumb_guid),
                )
            case DocumentHint(file_guid=guid, caption=caption, thumb_guid=thumb_guid):
                return DocumentContentView(
                    content=await self._resolve_bytes(guid),
                    caption=caption,
                    thumb=await self._resolve_bytes(thumb_guid),
                )
            case AnimationHint(file_guid=guid, caption=caption, thumb_guid=thumb_guid):
                return AnimationContentView(
                    content=await self._resolve_bytes(guid),
                    caption=caption,
                    thumb=await self._resolve_bytes(thumb_guid),
                )
            case VoiceHint(file_guid=guid, caption=caption):
                return VoiceContentView(content=await self._resolve_bytes(guid), caption=caption)
            case VideoNoteHint(file_guid=guid):
                return VideoNoteContentView(content=await self._resolve_bytes(guid))
            case ContactHint(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                vcard=vcard,
            ):
                return ContactHintView(
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name,
                    vcard=vcard,
                )
            case StickerHint(file_guid=guid):
                return StickerHintView(file_id=await self._resolve_file_id(guid))

    async def _resolve_bytes(self, guid: str | None) -> BinaryIO | None:
        if guid is None:
            return None
        file_info = await self.dao.get_by_guid(guid)
        content = await self.storage.get(file_info.file_content_link)
        content = BytesWithName(content.read(), original_filename=file_info.public_filename)
        return content


class BytesWithName(BytesIO):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.pop("original_filename", "")
        super().__init__(*args, **kwargs)

    @property
    def name(self) -> str:
        return self._name
