from dataclasses import dataclass
from datetime import datetime

from shvatka.core.models import dto
from shvatka.core.models.dto import hints


@dataclass
class CurrentHints:
    hints: list[hints.TimeHint]
    typed_keys: list[dto.KeyTime]
    level_number: int
    started_at: datetime


