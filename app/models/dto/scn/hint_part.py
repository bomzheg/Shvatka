from __future__ import annotations

import typing
from abc import ABC
from dataclasses import dataclass

from app.enums.hint_type import HintLiteral, HintType


class BaseHint(ABC):
    type: HintLiteral


@dataclass
class TextHint(BaseHint):
    text: str
    type: HintLiteral = HintType.text.name


@dataclass
class GPSHint(BaseHint):
    latitude: float
    longitude: float
    type: HintLiteral = HintType.gps.name


@dataclass
class ContactHint(BaseHint):
    phone_number: str
    first_name: str
    last_name: str = None
    vcard: str = None
    type: HintLiteral = HintType.contact.name


AnyHint: typing.TypeAlias = TextHint | GPSHint | ContactHint
