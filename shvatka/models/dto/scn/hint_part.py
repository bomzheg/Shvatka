from __future__ import annotations

import typing
from abc import ABC
from dataclasses import dataclass

from shvatka.models.enums.hint_type import HintLiteral, HintType


class BaseHint(ABC):
    type: HintLiteral


@dataclass
class TextHint(BaseHint):
    text: str
    type: HintLiteral = HintType.text.name


@dataclass
class LocationMixin:
    latitude: float
    longitude: float


@dataclass
class GPSHint(BaseHint, LocationMixin):
    type: HintLiteral = HintType.gps.name


@dataclass
class VenueHint(BaseHint, LocationMixin):
    title: str
    address: str
    foursquare_id: typing.Optional[str] = None
    foursquare_type: typing.Optional[str] = None
    type: HintLiteral = HintType.venue.name


@dataclass
class CaptionMixin:
    caption: str = None


@dataclass
class FileMixin:
    file_guid: str


@dataclass
class PhotoHint(BaseHint, CaptionMixin, FileMixin):
    type: HintLiteral = HintType.photo.name


@dataclass
class ThumbMixin:
    thumb_guid: str | None = None


@dataclass
class AudioHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: HintLiteral = HintType.audio.name


@dataclass
class VideoHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: HintLiteral = HintType.video.name


@dataclass
class DocumentHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: HintLiteral = HintType.document.name


@dataclass
class AnimationHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    type: HintLiteral = HintType.animation.name


@dataclass
class VoiceHint(BaseHint, CaptionMixin, FileMixin):
    type: HintLiteral = HintType.voice.name


@dataclass
class VideoNoteHint(BaseHint, FileMixin):
    type: HintLiteral = HintType.video_note.name


@dataclass
class ContactHint(BaseHint):
    phone_number: str
    first_name: str
    last_name: str = None
    vcard: str = None
    type: HintLiteral = HintType.contact.name


@dataclass
class StickerHint(BaseHint, FileMixin):
    type: HintLiteral = HintType.sticker.name


AnyHint: typing.TypeAlias = TextHint | GPSHint | VenueHint | ContactHint | \
                            PhotoHint | AudioHint | VideoHint | DocumentHint | \
                            AnimationHint | VoiceHint | VideoNoteHint | StickerHint
