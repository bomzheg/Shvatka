import re
from datetime import datetime
from typing import Optional

from app.utils import datetime_utils

KEY_PREFIXES = ("SH", "СХ")
KEY_PREFIXES_REGEXP = "|".join(KEY_PREFIXES)
KEY_REGEXP = re.compile(rf"^(?:{KEY_PREFIXES_REGEXP})[A-Z\dА-ЯЁ]+$")
LEVEL_ID_REGEXP = re.compile(r"[^a-zA-Z\d_-]")


def is_key_normal(key_expectant: str) -> Optional[str]:
    rez = re.search(KEY_REGEXP, key_expectant.strip())
    return None if rez is None else rez.group(0)


def is_multiple_keys_normal(keys: str) -> bool:
    """
    Возвращает True если в строке (keys) содержатся только правильные ключи,
    по одному на строку
    """
    return all(is_key_normal(key) is not None for key in keys.splitlines())


def is_level_id_correct(id_expectant: str) -> bool:
    return re.search(LEVEL_ID_REGEXP, id_expectant) is None


def date_from_text(text):
    try:
        return datetime.strptime(text, datetime_utils.DATE_FORMAT).date()
    except ValueError:
        raise ValueError(
            f"Строка <b>{text}</b> "
            f"не соответствует формату {datetime_utils.DATE_FORMAT_USER}, попробуй ещё раз."
        )


def time_from_text(text):
    try:
        return datetime.strptime(text, datetime_utils.TIME_FORMAT).time()
    except ValueError:
        raise ValueError(
            f"Строка <b>{text}</b> "
            f"не соответствует формату {datetime_utils.TIME_FORMAT_USER}, попробуй ещё раз."
        )
