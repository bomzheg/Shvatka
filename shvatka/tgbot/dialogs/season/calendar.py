from datetime import date
from typing import Any

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Calendar, CalendarScope, CalendarUserConfig
from aiogram_dialog.widgets.text import Text

FREE = "🟢"
TAKEN = "🔒"
MINE = "⭐"
LINKED = "🎮"


class SlotMark(Text):
    """A day cell that says what its date is, or just the number when it is free of one.

    The marks come from the window getter (`slot_marks`), which loads the season
    — or the draft being composed — once per render.
    """

    def __init__(self, *, today: bool = False) -> None:
        super().__init__()
        self.today = today

    async def _render_text(self, data: dict, manager: DialogManager) -> str:
        day: date = data["date"]
        marks: dict[str, str] = (data.get("data") or {}).get("slot_marks") or {}
        mark = marks.get(day.isoformat(), "")
        return f"[{mark}{day.day}]" if self.today else f"{mark}{day.day}"


class SeasonCalendar(Calendar):
    """The season's year as a calendar, with a mark on every planned date.

    The base widget renders a bare number per day; this one re-texts the days
    view so a cell reads the getter's marks, and pins the view to the season's
    year so no month outside it is reachable.
    """

    def _init_views(self) -> dict[CalendarScope, Any]:
        # the base class invites exactly this — "set Text widgets for buttons in
        # default views". Reaching into `kbd.calendar_kbd` for the view classes
        # would import a module that makes mypy mis-resolve an alias in
        # `widgets.common.scroll`, and `SmartScrollingGroup` uses that alias.
        views = super()._init_views()
        days: Any = views[CalendarScope.DAYS]
        days.date_text = SlotMark()
        days.today_text = SlotMark(today=True)
        return views

    async def _get_user_config(self, data: dict, manager: DialogManager) -> CalendarUserConfig:
        year = (data or {}).get("year")
        if not isinstance(year, int):
            return CalendarUserConfig()
        return CalendarUserConfig(
            min_date=date(year, 1, 1),
            max_date=date(year, 12, 31),
        )
