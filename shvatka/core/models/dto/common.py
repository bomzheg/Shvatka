from dataclasses import dataclass
from datetime import datetime


@dataclass
class DateRange:
    from_: datetime
    to: datetime | None
