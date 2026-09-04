import re
import unicodedata

from shvatka.core.utils.input_validation import validate_new_username

MAX_USERNAME_LENGTH = 50

CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "є": "ye",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "і": "i",
    "ї": "yi",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ў": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}

NOT_LATIN_OR_DIGIT = re.compile(r"[^a-z0-9]+")


def transliterate(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text.lower())
    latin = "".join(CYRILLIC_TO_LATIN.get(char, char) for char in normalized)
    decomposed = unicodedata.normalize("NFKD", latin)
    without_diacritics = "".join(char for char in decomposed if not unicodedata.combining(char))
    return NOT_LATIN_OR_DIGIT.sub("_", without_diacritics).strip("_")


def username_from_names(first_name: str | None, last_name: str | None) -> str | None:
    parts = [
        part for part in (transliterate(first_name or ""), transliterate(last_name or "")) if part
    ]
    if not parts:
        return None
    candidate = "_".join(parts)[:MAX_USERNAME_LENGTH].strip("_")
    return validate_new_username(candidate) if candidate else None


def numbered_username(username: str, number: int) -> str:
    suffix = f"_{number}"
    return username[: MAX_USERNAME_LENGTH - len(suffix)].rstrip("_") + suffix
