import enum


class HintType(enum.Enum):
    text = "text"
    gps = "gps"
    venue = "venue"
    photo = "photo"
    audio = "audio"
    video = "video"
    document = "document"
    animation = "animation"
    voice = "voice"
    video_note = "video_note"
    contact = "contact"
    sticker = "sticker"
