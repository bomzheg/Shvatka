from dataclasses import dataclass, field
from datetime import datetime

from shvatka.core.models import dto
from shvatka.core.models.dto import hints, action
from shvatka.core.games.input import InputContainer


@dataclass
class CurrentHints:
    hints: list[hints.TimeHint]
    typed_keys: list[dto.KeyTime]
    level_number: int
    started_at: datetime


@dataclass(kw_only=True)
class GamePlayResponse:
    input_container: InputContainer
    team: dto.Team
    game_finished: bool = False
    effects: list[action.Effects] = field(default_factory=list)
    wrong: bool = False
    new_key: dto.InsertedKey | None = None
