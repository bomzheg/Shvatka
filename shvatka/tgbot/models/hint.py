from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO

from aiogram.types import BufferedInputFile, InputFile


class BaseHintLinkView(ABC):
    @abstractmethod
    def kwargs(self) -> dict:
        raise NotImplementedError


class BaseHintContentView(ABC):
    @abstractmethod
    def kwargs(self) -> dict:
        raise NotImplementedError


@dataclass
class TextHintView(BaseHintLinkView, BaseHintContentView):
    text: str

    def kwargs(self) -> dict:
        return dict(text=self.text)


@dataclass
class GPSHintView(BaseHintLinkView, BaseHintContentView):
    latitude: float
    longitude: float

    def kwargs(self) -> dict:
        return dict(latitude=self.latitude, longitude=self.longitude)


@dataclass
class VenueHintView(BaseHintLinkView, BaseHintContentView):
    latitude: float
    longitude: float
    title: str
    address: str
    foursquare_id: str | None = None
    foursquare_type: str | None = None

    def kwargs(self) -> dict:
        return dict(
            latitude=self.latitude,
            longitude=self.longitude,
            title=self.title,
            address=self.address,
            foursquare_id=self.foursquare_id,
            foursquare_type=self.foursquare_type,
        )


@dataclass
class PhotoLinkView(BaseHintLinkView):
    file_id: str
    caption: str

    def kwargs(self) -> dict:
        return dict(photo=self.file_id, caption=self.caption)


@dataclass
class PhotoContentView(BaseHintContentView):
    content: BinaryIO
    caption: str

    def kwargs(self) -> dict:
        return dict(
            photo=_get_input_file(self.content),
            caption=self.caption,
        )


@dataclass
class AudioLinkView(BaseHintLinkView):
    file_id: str
    caption: str
    thumb: str | None

    def kwargs(self) -> dict:
        return dict(audio=self.file_id, caption=self.caption)


@dataclass
class AudioContentView(BaseHintContentView):
    content: BinaryIO
    caption: str
    thumb: BinaryIO | None

    def kwargs(self) -> dict:
        return dict(
            audio=_get_input_file(self.content),
            caption=self.caption,
            thumb=_get_input_file(self.thumb),
        )


@dataclass
class VideoLinkView(BaseHintLinkView):
    file_id: str
    caption: str
    thumb: str | None

    def kwargs(self) -> dict:
        return dict(video=self.file_id, caption=self.caption)


@dataclass
class VideoContentView(BaseHintContentView):
    content: BinaryIO
    caption: str
    thumb: BinaryIO | None

    def kwargs(self) -> dict:
        return dict(
            video=_get_input_file(self.content),
            caption=self.caption,
            thumb=_get_input_file(self.thumb),
        )


@dataclass
class DocumentLinkView(BaseHintLinkView):
    file_id: str
    caption: str
    thumb: str | None

    def kwargs(self) -> dict:
        return dict(document=self.file_id, caption=self.caption)


@dataclass
class DocumentContentView(BaseHintContentView):
    content: BinaryIO
    caption: str
    thumb: BinaryIO | None

    def kwargs(self) -> dict:
        return dict(
            document=_get_input_file(self.content),
            caption=self.caption,
            thumb=_get_input_file(self.thumb),
        )


@dataclass
class AnimationLinkView(BaseHintLinkView):
    file_id: str
    caption: str
    thumb: str | None

    def kwargs(self) -> dict:
        return dict(animation=self.file_id, caption=self.caption)


@dataclass
class AnimationContentView(BaseHintContentView):
    content: BinaryIO
    caption: str
    thumb: BinaryIO | None

    def kwargs(self) -> dict:
        return dict(
            animation=_get_input_file(self.content),
            caption=self.caption,
            thumb=_get_input_file(self.thumb),
        )


@dataclass
class VoiceLinkView(BaseHintLinkView):
    file_id: str
    caption: str

    def kwargs(self) -> dict:
        return dict(voice=self.file_id, caption=self.caption)


@dataclass
class VoiceContentView(BaseHintContentView):
    content: BinaryIO
    caption: str

    def kwargs(self) -> dict:
        return dict(
            voice=_get_input_file(self.content),
            caption=self.caption,
        )


@dataclass
class VideoNoteLinkView(BaseHintLinkView):
    file_id: str

    def kwargs(self) -> dict:
        return dict(video_note=self.file_id)


@dataclass
class VideoNoteContentView(BaseHintContentView):
    content: BinaryIO

    def kwargs(self) -> dict:
        return dict(video_note=_get_input_file(self.content))


@dataclass
class ContactHintView(BaseHintLinkView, BaseHintContentView):
    phone_number: str
    first_name: str
    last_name: str | None = None
    vcard: str | None = None

    def kwargs(self) -> dict:
        return dict(
            phone_number=self.phone_number,
            first_name=self.first_name,
            last_name=self.last_name,
            vcard=self.vcard,
        )


@dataclass
class StickerHintView(BaseHintLinkView, BaseHintContentView):
    file_id: str

    def kwargs(self) -> dict:
        return dict(sticker=self.file_id)


def _get_input_file(content: BinaryIO | None) -> InputFile | None:
    if content is None:
        return None
    return BufferedInputFile(file=content.read(), filename=content.name)
