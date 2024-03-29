import re
from datetime import datetime
from typing import Iterable

from shvatka.core.utils import datetime_utils
from shvatka.core.views.texts import KEY_PREFIXES

KEY_PREFIXES_REGEXP = "|".join(KEY_PREFIXES)
KEY_REGEXP = re.compile(rf"^(?:{KEY_PREFIXES_REGEXP})[A-Z\dА-ЯЁ]+$")
LEVEL_ID_REGEXP = re.compile(r"^[a-zA-Z\d_-]+$")


def is_key_valid(key_expectant: str) -> bool:
    return normalize_key(key_expectant) is not None


def normalize_key(key_expectant: str) -> str | None:
    rez = re.search(KEY_REGEXP, key_expectant.strip())
    return None if rez is None else rez.group(0)


def is_multiple_keys_normal(keys: Iterable[str]) -> bool:
    """
    Возвращает True если в строке (keys) содержатся только правильные ключи,
    по одному на строку
    """
    return all(map(is_key_valid, keys))


def validate_level_id(id_expectant: str) -> str | None:
    result = re.search(LEVEL_ID_REGEXP, id_expectant)
    return result.group() if result is not None else None


def date_from_text(text):
    try:
        return datetime.strptime(text, datetime_utils.DATE_FORMAT).date()
    except ValueError as e:
        raise ValueError(
            f"Строка <b>{text}</b> "
            f"не соответствует формату {datetime_utils.DATE_FORMAT_USER}, попробуй ещё раз."
        ) from e


def time_from_text(text):
    try:
        return datetime.strptime(text, datetime_utils.TIME_FORMAT).time()
    except ValueError as e:
        raise ValueError(
            f"Строка <b>{text}</b> "
            f"не соответствует формату {datetime_utils.TIME_FORMAT_USER}, попробуй ещё раз."
        ) from e
