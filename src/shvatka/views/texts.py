from src.shvatka.models.enums.hint_type import HintType
from src.shvatka.models.enums.played import Played

KEY_PREFIXES = ("SH", "СХ")

INVALID_KEY_ERROR = (
    f"Ключ должен содержать один из префиксов ({', '.join(KEY_PREFIXES)}), "
    f"использовать можно только цифры заглавные латинские и кириллические буквы "
)

WAIVER_STATUS_MEANING = {
    Played.yes: "Играют",
    Played.no: "Не играют",
    Played.think: "Размышляют",
}

HINTS_EMOJI: dict[HintType, str] = {
    HintType.text: "📃",
    HintType.gps: "📡",
    HintType.venue: "🧭",
    HintType.photo: "📷",
    HintType.audio: "🎼",
    HintType.video: "🎬",
    HintType.document: "📎",
    HintType.animation: "🌀",
    HintType.voice: "🎤",
    HintType.video_note: "🤳",
    HintType.contact: "🪪",
    HintType.sticker: "🏷",
}
PERMISSION_EMOJI = {True: "✅", False: "🚫"}
