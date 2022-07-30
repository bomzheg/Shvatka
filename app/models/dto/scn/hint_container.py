import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass

from aiogram import types
from aiogram.types.message import ContentType
from aiogram.utils.markdown import html_decoration as hd

from app.utils.exceptions import ScenarioNotCorrect
from .file_content import FileContent

T = typing.TypeVar('T')

_class_content = {
    ContentType.TEXT: 'text',
    ContentType.LOCATION: 'gps',
    ContentType.VENUE: 'venue',
    ContentType.PHOTO: 'photo',
    ContentType.AUDIO: 'audio',
    ContentType.VIDEO: 'video',
    ContentType.DOCUMENT: 'document',
    ContentType.ANIMATION: 'animation',
    ContentType.VOICE: 'voice',
    ContentType.VIDEO_NOTE: 'video_note',
    ContentType.CONTACT: 'contact',
    ContentType.STICKER: 'sticker',
}
supported_types = list(_class_content)


class BaseHint(ABC):
    content = ""

    def get_json_serializable(self) -> dict:
        return dict(**self._base_hint_json(), **self._special_json())

    @abstractmethod
    def _special_json(self) -> dict:
        pass

    def _base_hint_json(self) -> dict:
        return {
            "__hint__": True,
            "type": self.content
        }

    @property
    def kwargs(self):
        return self._special_json()

    @classmethod
    @abstractmethod
    def _save_content(cls, message: types.Message):
        pass

    @classmethod
    def _find_subclass(cls, content_type: str):
        for sub_class in cls.__subclasses__():
            # noinspection PyUnresolvedReferences
            if sub_class.content == content_type:
                return sub_class

    @classmethod
    def save_content(cls: typing.Type[T], message: types.Message) -> T:
        sub_class = cls._find_subclass(_class_content[message.content_type])
        # noinspection PyUnresolvedReferences
        # noinspection PyProtectedMember
        return sub_class._save_content(message)

    @classmethod
    def parse_as_hint(cls: typing.Type[T], dct: dict) -> T:
        if "__hint__" not in dct:
            raise ScenarioNotCorrect("hint without __hint__ key")
        content_type = dct["type"]
        if content_type not in _class_content.values():
            raise ScenarioNotCorrect(
                f"hint with unknown content_type: {content_type}"
            )
        sub_class = cls._find_subclass(content_type)
        # noinspection PyUnresolvedReferences
        # noinspection PyProtectedMember
        return sub_class._parse_as_hint(dct)

    @classmethod
    @abstractmethod
    def _parse_as_hint(cls, dct: dict):
        pass

    @property
    def has_file(self):
        return isinstance(self, FileMixin)


@dataclass
class TextHint(BaseHint):
    content = 'text'
    text: str

    def _special_json(self) -> dict:
        return {
            "text": self.text
        }

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(text=message.html_text)

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(text=dct["text"])

    def __repr__(self):
        return f"TextContainer(\"{self.text}\")"


@dataclass
class LocationMixin:
    latitude: float
    longitude: float


@dataclass
class GPSHint(BaseHint, LocationMixin):
    content = 'gps'

    def _special_json(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }

    @classmethod
    def _save_from_location(cls, location: types.Location):
        return cls(latitude=location.latitude, longitude=location.longitude)

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls._save_from_location(message.location)

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(latitude=float(dct["latitude"]), longitude=float(dct["longitude"]))


@dataclass
class VenueHint(BaseHint, LocationMixin):
    content = 'venue'
    title: str
    address: str
    foursquare_id: typing.Optional[str] = None
    foursquare_type: typing.Optional[str] = None

    def _special_json(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "title": self.title,
            "address": self.address,
            "foursquare_id": self.foursquare_id,
            "foursquare_type": self.foursquare_type
        }

    @classmethod
    def _save_from_venue(cls, venue: types.Venue):
        return cls(
            latitude=venue.location.latitude,
            longitude=venue.location.longitude,
            title=venue.title,
            address=venue.address,
            foursquare_id=venue.foursquare_id,
            foursquare_type=venue.foursquare_type
        )

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls._save_from_venue(message.venue)

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            latitude=float(dct["latitude"]),
            longitude=float(dct["longitude"]),
            title=dct["title"],
            address=dct["address"],
            foursquare_id=dct["foursquare_id"],
            foursquare_type=dct["foursquare_type"]
        )


@dataclass
class CaptionMixin:
    caption: typing.Optional[str] = None

    @property
    def caption_kwargs(self):
        return hd.quote(self.caption) if self.caption is not None else None


@dataclass
class ThumbMixin:
    thumb: typing.Optional[FileContent] = None

    def get_json_thumb(self):
        return None if self.thumb is None else self.thumb.get_json_serializable()

    @staticmethod
    def parse_as_thumb(dct: typing.Optional[dict]):
        return None if dct is None else FileContent.parse_as_file(dct)

    def get_thumb(self):
        return None if self.thumb is None else next(self.thumb.get_file())


@dataclass
class FileMixin:
    file: FileContent

    def file_kwargs(self):
        return self.file.file_kwargs()


@dataclass
class PhotoHint(BaseHint, CaptionMixin, FileMixin):
    content = 'photo'

    def _special_json(self) -> dict:
        return {
            "file": self.file.get_json_serializable(),
            "caption": self.caption,
        }

    @property
    def kwargs(self):
        return dict(caption=self.caption_kwargs)

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(file=FileContent(file_id=message.photo[-1].file_id, content=cls.content), caption=message.caption)

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            file=FileContent.parse_as_file(dct["file"]),
            caption=dct["caption"]
        )


@dataclass
class AudioHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    content = 'audio'

    def _special_json(self) -> dict:
        return {
            "file": self.file.get_json_serializable(),
            "caption": self.caption,
            "thumb": self.get_json_thumb()
        }

    @property
    def kwargs(self):
        return dict(caption=self.caption_kwargs, thumb=self.get_thumb())

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(
            file=FileContent(file_id=message.audio.file_id, content=cls.content),
            caption=message.caption,
            thumb=FileContent(file_id=message.audio.thumb.file_id) if message.audio.thumb is not None else None
        )

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            file=FileContent.parse_as_file(dct["file"]),
            caption=dct["caption"],
            thumb=cls.parse_as_thumb(dct["thumb"])
        )


@dataclass
class VideoHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    content = 'video'

    def _special_json(self) -> dict:
        return {
            "file": self.file.get_json_serializable(),
            "caption": self.caption,
            "thumb": self.get_json_thumb()
        }

    @property
    def kwargs(self):
        return dict(caption=self.caption_kwargs, thumb=self.get_thumb())

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(
            file=FileContent(file_id=message.video.file_id, content=cls.content),
            caption=message.caption,
            thumb=FileContent(file_id=message.video.thumb.file_id) if message.video.thumb is not None else None
        )

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            file=FileContent.parse_as_file(dct["file"]),
            caption=dct["caption"],
            thumb=cls.parse_as_thumb(dct["thumb"])
        )


@dataclass
class DocumentHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    content = 'document'

    def _special_json(self) -> dict:
        return {
            "file": self.file.get_json_serializable(),
            "caption": self.caption,
            "thumb": self.get_json_thumb()
        }

    @property
    def kwargs(self):
        return dict(caption=self.caption_kwargs, thumb=self.get_thumb())

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(
            file=FileContent(file_id=message.document.file_id, content=cls.content),
            caption=message.caption,
            thumb=FileContent(file_id=message.document.thumb.file_id) if message.document.thumb is not None else None
        )

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            file=FileContent.parse_as_file(dct["file"]),
            caption=dct["caption"],
            thumb=cls.parse_as_thumb(dct["thumb"])
        )


@dataclass
class AnimationHint(BaseHint, CaptionMixin, ThumbMixin, FileMixin):
    content = 'animation'

    def _special_json(self) -> dict:
        return {
            "file": self.file.get_json_serializable(),
            "caption": self.caption,
            "thumb": self.get_json_thumb()
        }

    @property
    def kwargs(self):
        return dict(caption=self.caption_kwargs, thumb=self.get_thumb())

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(
            file=FileContent(file_id=message.animation.file_id, content=cls.content),
            caption=message.caption,
            thumb=FileContent(file_id=message.animation.thumb.file_id) if message.animation.thumb is not None else None
        )

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            file=FileContent.parse_as_file(dct["file"]),
            caption=dct["caption"],
            thumb=cls.parse_as_thumb(dct["thumb"])
        )


@dataclass
class VoiceHint(BaseHint, CaptionMixin, FileMixin):
    content = 'voice'

    def _special_json(self) -> dict:
        return {
            "file": self.file.get_json_serializable(),
            "caption": self.caption
        }

    @property
    def kwargs(self):
        return dict(caption=self.caption_kwargs)

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(
            file=FileContent(file_id=message.voice.file_id, content=cls.content),
            caption=message.caption
        )

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            file=FileContent.parse_as_file(dct["file"]),
            caption=dct["caption"]
        )


@dataclass
class VideoNoteHint(BaseHint, ThumbMixin, FileMixin):
    content = 'video_note'

    def _special_json(self) -> dict:
        return {
            "file": self.file.get_json_serializable(),
            "thumb": self.get_json_thumb()
        }

    @property
    def kwargs(self):
        return dict(thumb=self.get_thumb())

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(
            file=FileContent(file_id=message.video_note.file_id, content=cls.content),
            thumb=FileContent(
                file_id=message.video_note.thumb.file_id) if message.video_note.thumb is not None else None
        )

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            file=FileContent.parse_as_file(dct["file"]),
            thumb=cls.parse_as_thumb(dct["thumb"])
        )


@dataclass
class ContactHint(BaseHint):
    content = 'contact'
    phone_number: str
    first_name: str
    last_name: str = None
    vcard: str = None

    def _special_json(self) -> dict:
        return {
            "phone_number": self.phone_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "vcard": self.vcard,
        }

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(
            phone_number=message.contact.phone_number,
            first_name=message.contact.first_name,
            last_name=message.contact.last_name,
            vcard=message.contact.vcard,
        )

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            phone_number=dct["phone_number"],
            first_name=dct["first_name"],
            last_name=dct["last_name"],
            vcard=dct["vcard"],
        )


@dataclass
class StickerHint(BaseHint):
    content = 'sticker'
    file_id: str

    def _special_json(self) -> dict:
        return {
            "sticker": self.file_id
        }

    @classmethod
    def _save_content(cls, message: types.Message):
        return cls(
            file_id=message.sticker.file_id,
        )

    @classmethod
    def _parse_as_hint(cls, dct: dict):
        return cls(
            file_id=dct["file_id"],
        )
