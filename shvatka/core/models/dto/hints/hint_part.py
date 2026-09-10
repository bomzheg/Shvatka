from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from shvatka.core.models.enums.hint_type import HintType
from shvatka.core.models.enums.rich_format import RichFormat


@dataclass(kw_only=True)
class LinkPreview:
    is_disabled: bool | None = None
    url: str | None = None
    prefer_small_media: bool | None = None
    prefer_large_media: bool | None = None
    show_above_text: bool | None = None


@dataclass(kw_only=True)
class BaseHint(ABC):
    type: str

    @abstractmethod
    def get_guids(self) -> list[str]:
        raise NotImplementedError


@dataclass(kw_only=True)
class TextHint(BaseHint):
    text: str
    type: Literal["text"] = HintType.text.name
    link_preview: LinkPreview | None = None

    def get_guids(self) -> list[str]:
        return []


@dataclass(kw_only=True)
class RichMedia:
    """A file embedded into the markup of a rich hint.

    The markup refers to the file by ``id`` (an ``<img src="id">`` in Rich HTML,
    an ``![](id)`` in Rich Markdown), while the game keeps the file itself under
    ``file_guid`` like any other hint file.
    """

    id: str
    file_guid: str


@dataclass(kw_only=True)
class RichHint(BaseHint):
    """A hint written as a rich message - headings, lists, tables and so on.

    ``text`` holds the markup itself, in the language named by ``format``.
    """

    text: str
    type: Literal["rich"] = HintType.rich.name
    format: RichFormat = RichFormat.html
    is_rtl: bool | None = None
    skip_entity_detection: bool | None = None
    media: list[RichMedia] = field(default_factory=list)

    def get_guids(self) -> list[str]:
        return [media.file_guid for media in self.media]


@dataclass(kw_only=True)
class LocationMixin:
    latitude: float
    longitude: float


@dataclass(kw_only=True)
class GPSHint(BaseHint, LocationMixin):
    type: Literal["gps"] = HintType.gps.name

    def get_guids(self) -> list[str]:
        return []


@dataclass(kw_only=True)
class VenueHint(BaseHint, LocationMixin):
    title: str
    address: str
    foursquare_id: str | None = None
    foursquare_type: str | None = None
    type: Literal["venue"] = HintType.venue.name

    def get_guids(self) -> list[str]:
        return []


@dataclass(kw_only=True)
class CaptionMixin:
    caption: str | None = None


@dataclass(kw_only=True)
class FileMixin:
    file_guid: str


@dataclass(kw_only=True)
class PhotoHint(BaseHint, CaptionMixin, FileMixin):
    type: Literal["photo"] = HintType.photo.name
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None

    def get_guids(self) -> list[str]:
        return [self.file_guid]


@dataclass(kw_only=True)
class ThumbMixin:
    thumb_guid: str | None = None

    def get_thumb_guid(self) -> list[str]:
        return [self.thumb_guid] if self.thumb_guid else []


@dataclass(kw_only=True)
class AudioHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: Literal["audio"] = HintType.audio.name

    def get_guids(self) -> list[str]:
        result = [self.file_guid]
        result.extend(self.get_thumb_guid())
        return result


@dataclass(kw_only=True)
class VideoHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: Literal["video"] = HintType.video.name
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None

    def get_guids(self) -> list[str]:
        result = [self.file_guid]
        result.extend(self.get_thumb_guid())
        return result


@dataclass(kw_only=True)
class DocumentHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: Literal["document"] = HintType.document.name

    def get_guids(self) -> list[str]:
        result = [self.file_guid]
        result.extend(self.get_thumb_guid())
        return result


@dataclass(kw_only=True)
class AnimationHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: Literal["animation"] = HintType.animation.name
    show_caption_above_media: bool | None = None
    has_spoiler: bool | None = None

    def get_guids(self) -> list[str]:
        result = [self.file_guid]
        result.extend(self.get_thumb_guid())
        return result


@dataclass(kw_only=True)
class VoiceHint(BaseHint, CaptionMixin, FileMixin):
    type: Literal["voice"] = HintType.voice.name

    def get_guids(self) -> list[str]:
        return [self.file_guid]


@dataclass(kw_only=True)
class VideoNoteHint(BaseHint, FileMixin):
    type: Literal["video_note"] = HintType.video_note.name

    def get_guids(self) -> list[str]:
        return [self.file_guid]


@dataclass(kw_only=True)
class ContactHint(BaseHint):
    phone_number: str
    first_name: str
    last_name: str | None = None
    vcard: str | None = None
    type: Literal["contact"] = HintType.contact.name

    def get_guids(self) -> list[str]:
        return []


@dataclass(kw_only=True)
class StickerHint(BaseHint, FileMixin):
    type: Literal["sticker"] = HintType.sticker.name

    def get_guids(self) -> list[str]:
        return [self.file_guid]


AnyHint: typing.TypeAlias = (
    TextHint
    | RichHint
    | GPSHint
    | VenueHint
    | ContactHint
    | PhotoHint
    | AudioHint
    | VideoHint
    | DocumentHint
    | AnimationHint
    | VoiceHint
    | VideoNoteHint
    | StickerHint
)
