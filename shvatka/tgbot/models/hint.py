from abc import ABC, abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import BinaryIO, Any

from aiogram import types
from aiogram.types import BufferedInputFile, InputFile

from shvatka.core.models import enums
from shvatka.core.models.dto import hints
from shvatka.core.models.dto.hints.hint_part import CaptionMixin
from shvatka.core.utils import exceptions

_MISSING = object()


@dataclass(kw_only=True)
class BaseHintView(ABC):
    def kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = self.specific_kwargs()
        return kwargs

    @abstractmethod
    def specific_kwargs(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(kw_only=True)
class BaseHintLinkView(BaseHintView, metaclass=ABCMeta):
    def is_file_id_missing(self) -> bool:
        """
        Only file-based views (photo, audio, video, ...) carry a ``file_id``
        attribute. When that attribute exists but is ``None`` the file was never
        uploaded to telegram, so we can't send by file_id and the sender must
        fall back to sending by content.

        Views without a ``file_id`` attribute at all (text, gps, venue, contact)
        have nothing to be missing - they are always sendable as a link, so the
        sentinel default keeps them out of the content fallback.
        """
        return getattr(self, "file_id", _MISSING) is None


@dataclass(kw_only=True)
class BaseHintContentView(BaseHintView, metaclass=ABCMeta):
    pass


@dataclass(kw_only=True)
class CaptionViewMixin(CaptionMixin, metaclass=ABCMeta):
    def caption_kwargs(self) -> dict[str, Any]:
        return {
            "caption": self.caption,
        }


@dataclass(kw_only=True)
class TextHintView(BaseHintLinkView, BaseHintContentView):
    text: str
    link_preview: hints.LinkPreview | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"text": self.text, "link_preview_options": _link_preview_to_tg(self.link_preview)}


@dataclass(kw_only=True)
class RichMediaView:
    """One file embedded in a rich message, either as a file_id or as bytes."""

    id: str
    content_type: enums.HintType | None
    file_id: str | None = None
    content: BinaryIO | None = None

    def to_tg(self) -> types.InputRichMessageMedia:
        return types.InputRichMessageMedia(id=self.id, media=self._media())

    def _media(self) -> types.InputRichMessageMediaUnion:
        media: str | InputFile
        if self.content is not None:
            media = _get_input_file(self.content)  # type: ignore[assignment]
        else:
            assert self.file_id is not None
            media = self.file_id
        match self.content_type:
            case enums.HintType.photo:
                return types.InputMediaPhoto(media=media)
            case enums.HintType.video:
                return types.InputMediaVideo(media=media)
            case enums.HintType.animation:
                return types.InputMediaAnimation(media=media)
            case enums.HintType.audio:
                return types.InputMediaAudio(media=media)
            case _:
                raise exceptions.UnsupportedFileFormat(
                    text=f"file {self.id} ({self.content_type}) "
                    f"can't be embedded into a rich message"
                )


@dataclass(kw_only=True)
class RichHintViewMixin(metaclass=ABCMeta):
    text: str
    format: enums.RichFormat
    is_rtl: bool | None = None
    skip_entity_detection: bool | None = None
    media: list[RichMediaView]

    def specific_kwargs(self) -> dict[str, Any]:
        return {"rich_message": self._rich_message()}

    def _rich_message(self) -> types.InputRichMessage:
        is_html = self.format == enums.RichFormat.html
        return types.InputRichMessage(
            html=self.text if is_html else None,
            markdown=None if is_html else self.text,
            is_rtl=self.is_rtl,
            skip_entity_detection=self.skip_entity_detection,
            media=[media.to_tg() for media in self.media] or None,
        )


@dataclass(kw_only=True)
class RichHintLinkView(RichHintViewMixin, BaseHintLinkView):
    def is_file_id_missing(self) -> bool:
        return any(media.file_id is None for media in self.media)


@dataclass(kw_only=True)
class RichHintContentView(RichHintViewMixin, BaseHintContentView):
    pass


@dataclass(kw_only=True)
class GPSHintView(BaseHintLinkView, BaseHintContentView):
    latitude: float
    longitude: float

    def specific_kwargs(self) -> dict[str, Any]:
        return {"latitude": self.latitude, "longitude": self.longitude}


@dataclass(kw_only=True)
class VenueHintView(BaseHintLinkView, BaseHintContentView):
    latitude: float
    longitude: float
    title: str
    address: str
    foursquare_id: str | None = None
    foursquare_type: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "title": self.title,
            "address": self.address,
            "foursquare_id": self.foursquare_id,
            "foursquare_type": self.foursquare_type,
        }


@dataclass(kw_only=True)
class PhotoLinkView(BaseHintLinkView, CaptionViewMixin):
    file_id: str | None
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "photo": self.file_id,
            "show_caption_above_media": self.show_caption_above_media,
            "has_spoiler": self.has_spoiler,
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class PhotoContentView(BaseHintContentView, CaptionViewMixin):
    content: BinaryIO
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "photo": _get_input_file(self.content),
            "show_caption_above_media": self.show_caption_above_media,
            "has_spoiler": self.has_spoiler,
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class AudioLinkView(BaseHintLinkView, CaptionViewMixin):
    file_id: str | None
    thumb: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "audio": self.file_id,
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class AudioContentView(BaseHintContentView, CaptionViewMixin):
    content: BinaryIO
    thumb: BinaryIO | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "audio": _get_input_file(self.content),
            "thumbnail": _get_input_file(self.thumb),
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class VideoLinkView(BaseHintLinkView, CaptionViewMixin):
    file_id: str | None
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None
    thumb: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "video": self.file_id,
            "show_caption_above_media": self.show_caption_above_media,
            "has_spoiler": self.has_spoiler,
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class VideoContentView(BaseHintContentView, CaptionViewMixin):
    content: BinaryIO
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None
    thumb: BinaryIO | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "video": _get_input_file(self.content),
            "show_caption_above_media": self.show_caption_above_media,
            "has_spoiler": self.has_spoiler,
            "thumbnail": _get_input_file(self.thumb),
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class DocumentLinkView(BaseHintLinkView, CaptionViewMixin):
    file_id: str | None
    thumb: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "document": self.file_id,
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class DocumentContentView(BaseHintContentView, CaptionViewMixin):
    content: BinaryIO
    thumb: BinaryIO | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "document": _get_input_file(self.content),
            "thumbnail": _get_input_file(self.thumb),
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class AnimationLinkView(BaseHintLinkView, CaptionViewMixin):
    file_id: str | None
    thumb: str | None = None
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "animation": self.file_id,
            "show_caption_above_media": self.show_caption_above_media,
            "has_spoiler": self.has_spoiler,
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class AnimationContentView(BaseHintContentView, CaptionViewMixin):
    content: BinaryIO
    thumb: BinaryIO | None = None
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "animation": _get_input_file(self.content),
            "show_caption_above_media": self.show_caption_above_media,
            "has_spoiler": self.has_spoiler,
            "thumbnail": _get_input_file(self.thumb),
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class VoiceLinkView(BaseHintLinkView, CaptionViewMixin):
    file_id: str | None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "voice": self.file_id,
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class VoiceContentView(BaseHintContentView, CaptionViewMixin):
    content: BinaryIO

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "voice": _get_input_file(self.content),
            **self.caption_kwargs(),
        }


@dataclass(kw_only=True)
class VideoNoteLinkView(BaseHintLinkView):
    file_id: str | None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"video_note": self.file_id}


@dataclass(kw_only=True)
class VideoNoteContentView(BaseHintContentView):
    content: BinaryIO

    def specific_kwargs(self) -> dict[str, Any]:
        return {"video_note": _get_input_file(self.content)}


@dataclass(kw_only=True)
class ContactHintView(BaseHintLinkView, BaseHintContentView):
    phone_number: str
    first_name: str
    last_name: str | None = None
    vcard: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "phone_number": self.phone_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "vcard": self.vcard,
        }


@dataclass(kw_only=True)
class StickerHintLinkView(BaseHintLinkView):
    file_id: str | None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"sticker": self.file_id}


@dataclass(kw_only=True)
class StickerHintContentView(BaseHintContentView):
    content: BinaryIO

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "sticker": _get_input_file(self.content),
        }


def _get_input_file(content: BinaryIO | None) -> InputFile | None:
    if content is None:
        return None
    return BufferedInputFile(file=content.read(), filename=content.name)


def _link_preview_to_tg(link_preview: hints.LinkPreview | None) -> types.LinkPreviewOptions | None:
    if link_preview is None:
        return None
    return types.LinkPreviewOptions(
        is_disabled=link_preview.is_disabled,
        url=link_preview.url,
        prefer_small_media=link_preview.prefer_small_media,
        prefer_large_media=link_preview.prefer_large_media,
        show_above_text=link_preview.show_above_text,
    )
