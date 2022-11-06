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


HINTS_EMOJI: dict[HintType: str] = {
    HintType.text: "📃",
    HintType.gps: "📡",
    HintType.venue: "🧭",
    HintType.photo: "🪪",
    HintType.audio: "📷",
    HintType.video: "🎼",
    HintType.document: "🎬",
    HintType.animation: "📎",
    HintType.voice: "🌀",
    HintType.video_note: "🎤",
    HintType.contact: "🤳",
    HintType.sticker: "🏷",
}
