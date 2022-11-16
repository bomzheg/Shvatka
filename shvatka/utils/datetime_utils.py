from dateutil import tz

DATE_FORMAT = r'%d.%m.%y'
DATE_FORMAT_USER = "dd.mm.yy"

TIME_FORMAT = r'%H:%M'
TIME_FORMAT_USER = "hh:mm"

DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
DATETIME_FORMAT_USER = f"{DATE_FORMAT_USER} {TIME_FORMAT_USER}"

GAME_LOCATION = 'Europe/Moscow'
tz_game = tz.gettz(GAME_LOCATION)
tz_utc = tz.gettz('UTC')
tz_local = tz.gettz()
