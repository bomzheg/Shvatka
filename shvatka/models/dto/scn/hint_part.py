from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from shvatka.models.enums.hint_type import HintType


class BaseHint(ABC):
    type: str

    @abstractmethod
    def get_guids(self) -> list[str]:
        raise NotImplementedError


@dataclass
class TextHint(BaseHint):
    text: str
    type: Literal["text"] = HintType.text.name

    def get_guids(self) -> list[str]:
        return []


@dataclass
class LocationMixin:
    latitude: float
    longitude: float


@dataclass
class GPSHint(BaseHint, LocationMixin):
    type: Literal["gps"] = HintType.gps.name

    def get_guids(self) -> list[str]:
        return []


@dataclass
class VenueHint(BaseHint, LocationMixin):
    title: str
    address: str
    foursquare_id: typing.Optional[str] = None
    foursquare_type: typing.Optional[str] = None
    type: Literal["venue"] = HintType.venue.name

    def get_guids(self) -> list[str]:
        return []


@dataclass
class CaptionMixin:
    caption: str = None


@dataclass
class FileMixin:
    file_guid: str


@dataclass
class PhotoHint(BaseHint, CaptionMixin, FileMixin):
    type: Literal["photo"] = HintType.photo.name

    def get_guids(self) -> list[str]:
        return [self.file_guid]


@dataclass
class ThumbMixin:
    thumb_guid: str | None = None

    def get_thumb_guid(self) -> list[str]:
        return [self.thumb_guid] if self.thumb_guid else []


@dataclass
class AudioHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: Literal["audio"] = HintType.audio.name

    def get_guids(self) -> list[str]:
        result = [self.file_guid]
        result.extend(self.get_thumb_guid())
        return result


@dataclass
class VideoHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: Literal["video"] = HintType.video.name

    def get_guids(self) -> list[str]:
        result = [self.file_guid]
        result.extend(self.get_thumb_guid())
        return result



@dataclass
class DocumentHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: Literal["document"] = HintType.document.name

    def get_guids(self) -> list[str]:
        result = [self.file_guid]
        result.extend(self.get_thumb_guid())
        return result


@dataclass
class AnimationHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: Literal["animation"] = HintType.animation.name

    def get_guids(self) -> list[str]:
        result = [self.file_guid]
        result.extend(self.get_thumb_guid())
        return result


@dataclass
class VoiceHint(BaseHint, CaptionMixin, FileMixin):
    type: Literal["voice"] = HintType.voice.name

    def get_guids(self) -> list[str]:
        return [self.file_guid]


@dataclass
class VideoNoteHint(BaseHint, FileMixin):
    type: Literal["video_note"] = HintType.video_note.name

    def get_guids(self) -> list[str]:
        return [self.file_guid]


@dataclass
class ContactHint(BaseHint):
    phone_number: str
    first_name: str
    last_name: str = None
    vcard: str = None
    type: Literal["contact"] = HintType.contact.name

    def get_guids(self) -> list[str]:
        return []


@dataclass
class StickerHint(BaseHint, FileMixin):
    type: Literal["sticker"] = HintType.sticker.name

    def get_guids(self) -> list[str]:
        return []


AnyHint: typing.TypeAlias = TextHint | GPSHint | VenueHint | ContactHint | \
                            PhotoHint | AudioHint | VideoHint | DocumentHint | \
                            AnimationHint | VoiceHint | VideoNoteHint | StickerHint
