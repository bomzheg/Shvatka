from shvatka.core.models.dto import action
from shvatka.core.models.enums.hint_type import HintType
from shvatka.core.models.enums.played import Played
from shvatka.tgbot.views.utils import render_hints

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


def render_effects(effects: action.Effects | None) -> str:
    if effects is None:
        return ""
    result = ""
    if effects.next_level:
        result += "🔀"
    elif effects.level_up:
        result += "🚩"
    if effects.bonus_minutes:
        result += "💰"
    if effects.hints_:
        result += f"[{render_hints(effects.hints_)}]"
    return result
