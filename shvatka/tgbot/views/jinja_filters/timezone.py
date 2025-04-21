from datetime import datetime, timedelta

from shvatka.core.utils.datetime_utils import tz_game, DATETIME_FORMAT, TIME_FORMAT


def time_user_timezone(value: datetime | None) -> str:
    return datetime_filter(value, format_=TIME_FORMAT)


def datetime_filter(value: datetime | None, format_: str = DATETIME_FORMAT) -> str:
    if value is None:
        return "n/a"
    local_dt = value.astimezone(tz_game)
    return local_dt.strftime(format_)


def timedelta_filter(value: timedelta) -> str:
    mins = value.seconds // 60
    return f"{mins} мин."
