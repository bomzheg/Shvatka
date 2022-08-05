import enum
import typing

HintLiteral = typing.Literal[
    "text",
    "gps",
    # "venue",
    # "photo",
    # "audio",
    # "video",
    # "document",
    # "animation",
    # "voice",
    # "video_note",
    "contact",
    # "sticker",
]


# noinspection PyArgumentList
class HintType(enum.Enum):
    text = "text"
    gps = "gps"
    # venue = "venue"
    # photo = "photo"
    # audio = "audio"
    # video = "video"
    # document = "document"
    # animation = "animation"
    # voice = "voice"
    # video_note = "video_note"
    contact = "contact"
    # sticker = "sticker"
