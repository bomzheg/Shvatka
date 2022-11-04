from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO

from aiogram.types import BufferedInputFile


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
            photo=BufferedInputFile(file=self.content.read(), filename=self.content.name),
            caption=self.caption,
        )


@dataclass
class ContactHintView(BaseHintLinkView, BaseHintContentView):
    phone_number: str
    first_name: str
    last_name: str = None
    vcard: str = None

    def kwargs(self) -> dict:
        return dict(
            phone_number=self.phone_number,
            first_name=self.first_name,
            last_name=self.last_name,
            vcard=self.vcard,
        )
