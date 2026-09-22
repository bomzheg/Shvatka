"""The season calendar: aiogram_dialog's `Calendar`, with a mark on a day.

Nothing here imports `aiogram_dialog.widgets.kbd.calendar_kbd`. Pulling that
submodule into mypy's graph makes it mis-resolve `OnPageChangedVariants` in the
library's own `widgets.common.scroll`, which turns `tgbot/dialogs/paging.py`
red — a file this change never touched. So the days view is the one the base
class hands back, re-texted, and every name comes from the `kbd` package.
"""

from __future__ import annotations

import typing
from datetime import date, timezone

from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.kbd import Calendar, CalendarConfig, CalendarScope, CalendarUserConfig
from aiogram_dialog.widgets.text import Text

from shvatka.core.utils.datetime_utils import tz_game

MARKS_KEY = "marks"
"""What the window getter calls the day → mark mapping it hands the calendar."""

YEAR_KEY = "year"
"""Where the season's year lives in `dialog_data`, so the view can be pinned."""


class SlotDayText(Text):
    """A day cell: the season's mark for that day, or a plain number."""

    def __init__(self, *, today: bool = False) -> None:
        super().__init__()
        self.today = today

    async def _render_text(self, data: dict, manager: DialogManager) -> str:
        day: date = data["date"]
        window_data = data.get("data") or {}
        mark = (window_data.get(MARKS_KEY) or {}).get(day.isoformat())
        number = f"[{day.day}]" if self.today else str(day.day)
        return f"{mark}{number}" if mark else number


class SeasonCalendar(Calendar):
    """A year of the schedule: marked days, and nothing outside the season."""

    def _init_views(self) -> dict[CalendarScope, typing.Any]:
        views = super()._init_views()
        days = views[CalendarScope.DAYS]
        # re-text the base view rather than build one: the library's view
        # classes live in the submodule this module must not import
        days.date_text = SlotDayText()  # type: ignore[attr-defined]
        days.today_text = SlotDayText(today=True)  # type: ignore[attr-defined]
        return views

    async def _get_user_config(self, data: dict, manager: DialogManager) -> CalendarUserConfig:
        year = _year(manager)
        if year is None:
            return CalendarUserConfig()
        # a season *is* a year: a date outside it would be invisible in both
        # edges, and the engine refuses one anyway
        return CalendarUserConfig(min_date=date(year, 1, 1), max_date=date(year, 12, 31))

    def get_scope(self, manager: DialogManager) -> CalendarScope:
        if not self.get_widget_data(manager, {}).get("current_scope"):
            # the months are the entry point, so a whole season is two taps away
            return CalendarScope.MONTHS
        return super().get_scope(manager)

    def get_offset(self, manager: DialogManager) -> date | None:
        offset = super().get_offset(manager)
        year = _year(manager)
        if year is None or (offset is not None and offset.year == year):
            return offset
        # the widget remembers a month, the dialog remembers a year: switching
        # the year has to drag the view along, or it shows somebody else's season
        return date(year, offset.month if offset else 1, 1)


def _year(manager: DialogManager) -> int | None:
    year = manager.dialog_data.get(YEAR_KEY)
    return int(year) if year is not None else None


SEASON_CALENDAR_CONFIG = CalendarConfig(
    firstweekday=0,
    # `CalendarConfig` is annotated with `timezone`, but only ever passes this
    # to `datetime.now`, which any `tzinfo` satisfies
    timezone=typing.cast(timezone, tz_game),
)
