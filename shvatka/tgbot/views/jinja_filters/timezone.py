from datetime import datetime

from shvatka.core.utils.datetime_utils import tz_game, DATETIME_FORMAT


def datetime_filter(value: datetime, format_: str = DATETIME_FORMAT) -> str:
    local_dt = value.astimezone(tz_game)
    return local_dt.strftime(format_)
