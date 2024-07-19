from datetime import datetime, timedelta

from shvatka.core.utils.datetime_utils import tz_game, DATETIME_FORMAT


def datetime_filter(value: datetime, format_: str = DATETIME_FORMAT) -> str:
    local_dt = value.astimezone(tz_game)
    return local_dt.strftime(format_)


def timedelta_filter(value: timedelta) -> str:
    mins = value.seconds // 60
    secs = value.seconds % 60
    return f"{mins} мин. {secs} сек."
