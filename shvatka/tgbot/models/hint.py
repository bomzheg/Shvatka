from abc import ABC, abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import BinaryIO, Any

from aiogram import types
from aiogram.types import BufferedInputFile, InputFile

from shvatka.core.models.dto import hints


@dataclass(kw_only=True)
class BaseHintView(ABC):
    link_preview: hints.LinkPreview | None = None

    def kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = self.specific_kwargs()
        if self.link_preview:
            kwargs["link_preview_options"] = _link_preview_to_tg(self.link_preview)
        return kwargs

    @abstractmethod
    def specific_kwargs(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(kw_only=True)
class BaseHintLinkView(BaseHintView, metaclass=ABCMeta):
    pass


@dataclass(kw_only=True)
class BaseHintContentView(BaseHintView, metaclass=ABCMeta):
    pass


@dataclass(kw_only=True)
class TextHintView(BaseHintLinkView, BaseHintContentView):
    text: str

    def specific_kwargs(self) -> dict[str, Any]:
        return {"text": self.text}


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
class PhotoLinkView(BaseHintLinkView):
    file_id: str
    caption: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"photo": self.file_id, "caption": self.caption}


@dataclass(kw_only=True)
class PhotoContentView(BaseHintContentView):
    content: BinaryIO
    caption: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "photo": _get_input_file(self.content),
            "caption": self.caption,
        }


@dataclass(kw_only=True)
class AudioLinkView(BaseHintLinkView):
    file_id: str
    caption: str | None = None
    thumb: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"audio": self.file_id, "caption": self.caption}


@dataclass(kw_only=True)
class AudioContentView(BaseHintContentView):
    content: BinaryIO
    caption: str | None = None
    thumb: BinaryIO | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "audio": _get_input_file(self.content),
            "caption": self.caption,
            "thumbnail": _get_input_file(self.thumb),
        }


@dataclass(kw_only=True)
class VideoLinkView(BaseHintLinkView):
    file_id: str
    caption: str | None = None
    thumb: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"video": self.file_id, "caption": self.caption}


@dataclass(kw_only=True)
class VideoContentView(BaseHintContentView):
    content: BinaryIO
    caption: str | None = None
    thumb: BinaryIO | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "video": _get_input_file(self.content),
            "caption": self.caption,
            "thumbnail": _get_input_file(self.thumb),
        }


@dataclass(kw_only=True)
class DocumentLinkView(BaseHintLinkView):
    file_id: str
    caption: str | None = None
    thumb: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"document": self.file_id, "caption": self.caption}


@dataclass(kw_only=True)
class DocumentContentView(BaseHintContentView):
    content: BinaryIO
    caption: str | None = None
    thumb: BinaryIO | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "document": _get_input_file(self.content),
            "caption": self.caption,
            "thumbnail": _get_input_file(self.thumb),
        }


@dataclass(kw_only=True)
class AnimationLinkView(BaseHintLinkView):
    file_id: str
    caption: str | None = None
    thumb: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"animation": self.file_id, "caption": self.caption}


@dataclass(kw_only=True)
class AnimationContentView(BaseHintContentView):
    content: BinaryIO
    caption: str | None = None
    thumb: BinaryIO | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "animation": _get_input_file(self.content),
            "caption": self.caption,
            "thumbnail": _get_input_file(self.thumb),
        }


@dataclass(kw_only=True)
class VoiceLinkView(BaseHintLinkView):
    file_id: str
    caption: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {"voice": self.file_id, "caption": self.caption}


@dataclass(kw_only=True)
class VoiceContentView(BaseHintContentView):
    content: BinaryIO
    caption: str | None = None

    def specific_kwargs(self) -> dict[str, Any]:
        return {
            "voice": _get_input_file(self.content),
            "caption": self.caption,
        }


@dataclass(kw_only=True)
class VideoNoteLinkView(BaseHintLinkView):
    file_id: str

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
class StickerHintView(BaseHintLinkView, BaseHintContentView):
    file_id: str

    def specific_kwargs(self) -> dict[str, Any]:
        return {"sticker": self.file_id}


def _get_input_file(content: BinaryIO | None) -> InputFile | None:
    if content is None:
        return None
    return BufferedInputFile(file=content.read(), filename=content.name)


def _link_preview_to_tg(link_preview: hints.LinkPreview) -> types.LinkPreviewOptions:
    return types.LinkPreviewOptions(
        is_disabled=link_preview.is_disabled,
        url=link_preview.url,
        prefer_small_media=link_preview.prefer_small_media,
        prefer_large_media=link_preview.prefer_large_media,
        show_above_text=link_preview.show_above_text,
    )
