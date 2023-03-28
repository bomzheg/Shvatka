import typing
from datetime import datetime, tzinfo

from dateutil import tz

DATE_FORMAT = r"%d.%m.%y"
DATE_FORMAT_USER = "dd.mm.yy"

TIME_FORMAT = r"%H:%M"
TIME_FORMAT_USER = "hh:mm"

DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
DATETIME_FORMAT_USER = f"{DATE_FORMAT_USER} {TIME_FORMAT_USER}"

GAME_LOCATION = "Europe/Moscow"


def get_tz(location: str) -> tzinfo:
    result = tz.gettz(location)
    assert result is not None
    return result


tz_game = get_tz(GAME_LOCATION)
tz_utc = get_tz("UTC")
tz_local = typing.cast(tzinfo, tz.gettz())


def add_timezone(dt: datetime, timezone: tzinfo = tz_game) -> datetime:
    return datetime.combine(dt.date(), dt.time(), timezone)
