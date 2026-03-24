from typing import Sequence

from shvatka.core.models.dto import action, hints
from shvatka.core.models.enums.hint_type import HintType
from shvatka.core.models.enums.played import Played
from shvatka.core.utils.input_validation import KEY_PREFIXES

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


def render_time_hints(time_hints: list[hints.TimeHint]) -> str:
    return "\n".join([render_time_hint(time_hint) for time_hint in time_hints])


def render_time_hint(time_hint: hints.TimeHint) -> str:
    return f"{time_hint.time}: {render_hints(time_hint.hint)}"


def render_hints(hints_: Sequence[hints.AnyHint]) -> str:
    return "".join([render_single_hint(hint) for hint in hints_])


def render_single_hint(hint: hints.AnyHint) -> str:
    return HINTS_EMOJI[HintType[hint.type]]
