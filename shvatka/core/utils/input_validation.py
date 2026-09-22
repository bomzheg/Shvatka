import re
from collections.abc import Iterable
from datetime import datetime

from shvatka.core.utils import datetime_utils
from shvatka.core.utils.key_folding import fold_key

KEY_PREFIXES = ("SH", "СХ")
FOLDED_KEY_PREFIXES = tuple(dict.fromkeys(fold_key(prefix) for prefix in KEY_PREFIXES))
KEY_PREFIXES_REGEXP = "|".join(FOLDED_KEY_PREFIXES)
#: Matches a key already passed through `fold_key`, so a prefix or a body typed
#: in the other alphabet is the same key as the one the author wrote.
FOLDED_KEY_REGEXP = re.compile(rf"^(?:{KEY_PREFIXES_REGEXP})[A-Z\dА-ЯЁ]+$")
LEVEL_ID_REGEXP = re.compile(r"^[a-zA-Z\d_-]+$")
USERNAME_REGEXP = re.compile(r"^[a-zA-Z\d_]{3,50}$")
EMAIL_REGEXP = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_key_valid(key_expectant: str) -> bool:
    return normalize_key(key_expectant) is not None


def normalize_key(key_expectant: str) -> str | None:
    key = key_expectant.strip()
    return key if re.search(FOLDED_KEY_REGEXP, fold_key(key)) else None


def is_multiple_keys_normal(keys: Iterable[str]) -> bool:
    """
    Возвращает True если в строке (keys) содержатся только правильные ключи,
    по одному на строку
    """
    return all(map(is_key_valid, keys))


def validate_level_id(id_expectant: str) -> str | None:
    result = re.search(LEVEL_ID_REGEXP, id_expectant)
    return result.group() if result is not None else None


def validate_new_username(username_expectant: str) -> str | None:
    result = re.search(USERNAME_REGEXP, username_expectant.strip())
    return result.group() if result is not None else None


def validate_email(email_expectant: str) -> str | None:
    normalized = email_expectant.strip().lower()
    result = re.search(EMAIL_REGEXP, normalized)
    return normalized if result is not None else None


def date_from_text(text):
    try:
        return datetime.strptime(text, datetime_utils.DATE_FORMAT).date()  # noqa: DTZ007
    except ValueError as e:
        raise ValueError(
            f"Строка <b>{text}</b> "
            f"не соответствует формату {datetime_utils.DATE_FORMAT_USER}, попробуй ещё раз."
        ) from e


def time_from_text(text):
    try:
        return datetime.strptime(text, datetime_utils.TIME_FORMAT).time()  # noqa: DTZ007
    except ValueError as e:
        raise ValueError(
            f"Строка <b>{text}</b> "
            f"не соответствует формату {datetime_utils.TIME_FORMAT_USER}, попробуй ещё раз."
        ) from e
